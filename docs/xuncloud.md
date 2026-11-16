# XunCloud account synchronization

The desktop bottom toolbar and Quick UI include **Connect cloud account**. This opens the local core's Web GUI at `?cloud=join` without placing an API key or cloud password in the URL. A remote tray profile is not a substitute for the local device's sync core.

The server creates ordinary user accounts. After login the client configures the server device and a personal folder automatically. Only devices signed in to the same account share that folder, through the server. This does not grant server GUI access.

## Standalone core (desktop)

Build the adjacent `xun-cloud` core, select it in Settings → Internal / launcher, and leave **Use built-in Syncthing library** unchecked. Alternatively connect Tray to an already-running local account-aware core. Disable upstream automatic binary updates for downstream builds.

## Built-in core (including the Qt Android variant)

The upstream libsyncthing fork has C bindings and logging/CLI changes not present in `xun-cloud`. Do **not** point `SYNCTHING_PATH` directly to the latter or modify submodule contents. Stage a combined build source instead, from this repository:

```sh
python3 scripts/prepare-xuncloud-core.py \
  --cloud-source ../xun-cloud --output tmp/xuncloud-core
```

Configure the normal CMake build with `-DSYNCTHING_PATH=<absolute path to tmp/xuncloud-core>`. The script refuses an existing destination, preserves the fork-specific C bindings, adds only the account client/API/GUI integration, and fails if integration anchors no longer match. Re-run to a new staging path after changing account code. The server itself is built from `xun-cloud`, not this staging fork.

Use the normal Qt/CMake/NDK build dependencies and platform packaging process. For a private server CA, the core supports `XUNCLOUD_CA_FILE`; otherwise it uses system trust. Never disable TLS validation. Android still needs storage/background permissions. In a Unix-domain-socket-only GUI configuration, the browser entry is hidden; use a loopback HTTP(S) GUI for browser enrollment.

On the current Mac, the staged Go client/API tests and C-archive compilation passed. The full Qt application and Android APK require toolchains not installed here; no release or real-device certification is implied.

See `../../xun-cloud/docs/cloud-accounts.md` for server deployment, port/HTTPS requirements, account and device revocation limitations. Old installed binaries do not gain this feature from menu changes alone.
