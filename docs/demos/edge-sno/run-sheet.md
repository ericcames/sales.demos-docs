# Run sheet — Edge / Single Node OpenShift

**This is the page you hold while building.** Three phases, from bare hardware
to the same OCP Virt demo that runs on RHDP. Once the environment is up,
present from the [OCP Virt run sheet](../openshift-virtualization/run-sheet.md).

| | |
|---|---|
| **Hands-on time** | ~90 minutes (spread across the three phases) |
| **Wall-clock time** | ~2.5 hours (the cluster installs unattended for ~45 minutes) |
| **Hardware** | x86_64, 32 GB+ RAM, 120 GB+ disk, 8+ CPUs |
| **Repos** | `image.builder.pipeline` (Phase 1), `sales.demos` (Phase 3) |

---

## Before you start

### One-time prerequisites

- [ ] Red Hat pull secret downloaded from
      [console.redhat.com](https://console.redhat.com/openshift/install/pull-secret)
      (save as `~/pull-secret.json`)
- [ ] SSH key pair exists (`~/.ssh/id_ed25519.pub`)
- [ ] Both repos cloned:
      ```bash
      git clone https://github.com/ericcames/image.builder.pipeline.git
      git clone https://github.com/ericcames/sales.demos.git
      ```
- [ ] Ansible collections installed:
      ```bash
      cd sales.demos
      ansible-galaxy collection install -r requirements.yml
      ```
- [ ] Vault password file at `~/secrets/.vault_pass_sales_demos`
- [ ] Secrets file created from the example:
      ```bash
      cp playbooks/group_vars/all/secrets.yml.example \
         playbooks/group_vars/all/secrets.yml
      ansible-vault encrypt playbooks/group_vars/all/secrets.yml \
        --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
      ```

### Hardware details you will need

Gather these before you begin — every value is required by `generate-iso.sh`:

| What | How to find it | Example |
|---|---|---|
| IP address (CIDR) | Your network plan | `192.168.1.100/24` |
| Gateway | `ip route show default` on any machine on the network | `192.168.1.1` |
| DNS server | Usually the gateway | `192.168.1.1` |
| MAC address | Check BIOS, or `ip link` if an OS is already installed | `1c:69:7a:0d:50:30` |
| NIC name | `ip link` — the physical interface, not `lo` | `eno1` |
| Disk device | `lsblk` — the primary disk | `/dev/sda` |
| Hostname | Your choice | `nuc01` |

---

## Phase 1 — Build the ISO (~10 minutes)

**Repo: `image.builder.pipeline`**

```bash
cd image.builder.pipeline

bash playbooks/scripts/generate-iso.sh \
  --pull-secret ~/pull-secret.json \
  --ssh-key ~/.ssh/id_ed25519.pub \
  --hostname <hostname> \
  --ip <ip/cidr> \
  --gateway <gateway> \
  --dns <dns> \
  --interface <nic> \
  --disk <disk> \
  --mac <mac> \
  --cluster-name <cluster-name> \
  --base-domain <base-domain>
```

The script outputs the path to the generated ISO.

### Write to USB

```bash
sudo dd if=<path-to-iso>/agent.x86_64.iso of=/dev/sdX bs=4M status=progress
sync
```

!!! warning
    Double-check the target device (`/dev/sdX`). `dd` will overwrite
    whatever you point it at.

---

## Phase 2 — Boot and install (~45 minutes, unattended)

1. **Set up DNS first.** The cluster needs `api.<cluster>.<domain>` and
   `*.apps.<cluster>.<domain>` to resolve to the node's IP. On a Fedora laptop
   with systemd-resolved:

    ```bash
    # dnsmasq config — one wildcard covers everything
    sudo tee /etc/dnsmasq.d/sno.conf <<EOF
    address=/<cluster-name>.<base-domain>/<node-ip>
    listen-address=127.0.0.2
    bind-interfaces
    server=<gateway-ip>
    EOF

    # Route the domain to dnsmasq
    sudo mkdir -p /etc/systemd/resolved.conf.d
    sudo tee /etc/systemd/resolved.conf.d/sno.conf <<EOF
    [Resolve]
    DNS=127.0.0.2
    Domains=~<base-domain>
    EOF

    sudo systemctl enable --now dnsmasq
    sudo systemctl restart systemd-resolved
    ```

2. **Verify DNS resolves:**

    ```bash
    dig +short api.<cluster-name>.<base-domain>
    dig +short console.apps.<cluster-name>.<base-domain>
    ```

    Both should return the node's IP.

3. **Boot the hardware from USB.** Enter BIOS/UEFI, set USB as the boot device.
   The Agent-Based Installer runs unattended.

4. **Wait.** The install takes about 45 minutes. You can monitor progress if you
   have console access, but it requires no input.

5. **Verify the cluster is up:**

    ```bash
    export KUBECONFIG=<workdir>/auth/kubeconfig
    oc get nodes
    oc get clusterversion
    ```

### Generate a kubeconfig for sales.demos

```bash
cd sales.demos
bash utilities/make-kubeconfig.sh edge
```

This creates `.kube/edge.kubeconfig` from the cluster's connection details.

---

## Phase 3 — Configure the platform (~20 minutes)

**Repo: `sales.demos`**

### Step 1 — Run `setup_edge.yml`

!!! note
    `install_aap.yml` is tracked in
    [sales.demos#395](https://github.com/ericcames/sales.demos/issues/395).
    Until it ships, deploy AAP manually by creating the
    `AnsibleAutomationPlatform` CR. See the
    [architecture doc](architecture.md#manual-aap-deployment) for the CR spec.

```bash
ansible-playbook playbooks/setup_edge.yml \
  -i inventory --limit edge \
  -e target_env=edge \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos \
  2>&1 | tee /tmp/setup-edge-$(date +%Y%m%d-%H%M).log
```

This runs five stages:

| Stage | Playbook | Time |
|---|---|---|
| 1 | `install_lvms.yml` — LVMS operator + LVMCluster CR | ~2 min |
| 2 | `install_aap.yml` — deploy AAP from operator | ~20 min |
| 3 | `install_cnv.yml` — OpenShift Virtualization | ~4 min |
| 4 | `install_compliance.yml` — Compliance Operator | ~2 min |
| 5 | `prepare_env.yml` — prove it by building a real VM | ~1 min |

### Step 2 — Update the vault with the AAP admin password

`install_aap.yml` prints the operator-generated admin password. Add it to
the vault:

```bash
ansible-vault edit playbooks/group_vars/all/secrets.yml \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

Set `env_secrets.edge.aap_password` to the printed value.

### Step 3 — Apply the AAP configuration

```bash
ansible-playbook playbooks/config.yml \
  -i inventory --limit edge \
  -e target_env=edge \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos \
  2>&1 | tee /tmp/config-edge-$(date +%Y%m%d-%H%M).log
```

This creates the organizations, credentials, projects, job templates,
inventories, and schedules — the same CaC that runs on RHDP.

### Step 4 — Deploy Grafana Alloy (optional)

```bash
ansible-playbook playbooks/deploy_alloy.yml \
  -i inventory --limit edge \
  -e target_env=edge \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

Pushes metrics and logs to Grafana Cloud. Requires `grafana_cloud_*`
credentials in the vault.

### Step 5 — Provision demo VMs

Launch **`Linux Day 1 - 0 Workflow`** from AAP, or:

```bash
ansible-playbook playbooks/provision_vm.yml \
  -i inventory --limit edge \
  -e target_env=edge \
  -e os_type=linux -e vm_size_tier=large \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

---

## Verification checklist

- [ ] `oc get nodes` shows one node, `Ready`
- [ ] `oc get csv -A` shows AAP, CNV, LVMS, Compliance operators `Succeeded`
- [ ] AAP gateway is reachable at `https://aap-aap.apps.<cluster>.<domain>`
- [ ] `Linux Day 1 - 0 Workflow` exists in AAP (workflows are shared config, so `config.yml` creates it on `edge` too)
- [ ] A test VM provisions and the demo page returns 200

---

## Recovery moves

| Symptom | Move |
|---|---|
| DNS does not resolve | Check dnsmasq is running: `systemctl status dnsmasq`. Verify the `.conf` files match your cluster name and IP |
| Cluster install hangs past 60 minutes | Attach a monitor. Common causes: wrong disk device, NIC name mismatch, DHCP conflict with static IP |
| `install_lvms.yml` — PVCs stuck Pending | The LVMS partition (partition 5) was not created. Rebuild the ISO with `--disk` pointing at the correct device |
| AAP components not reaching Ready | Check events: `oc get events -n aap --sort-by=.lastTimestamp`. Storage issues are the usual cause on SNO — verify `lvms-vg1` StorageClass exists |
| `config.yml` fails with 503 | AAP is still settling after deployment. Wait 5-10 minutes and retry. A fresh AAP deployment can peg CPU briefly |
| RHDP token errors | Not applicable — edge uses ServiceAccount tokens, not RHDP OAuth. If you see 401s, regenerate the token: `oc create token <sa>` |

---

## Teardown

To destroy demo VMs while preserving the platform:

```bash
ansible-playbook playbooks/teardown.yml \
  -i inventory --limit edge \
  -e target_env=edge \
  --vault-id sales.demos@~/secrets/.vault_pass_sales_demos
```

This removes the VMs and deregisters them from AAP. OpenShift Virtualization,
AAP, LVMS, boot sources, and the Terraform state namespace are deliberately
preserved.
