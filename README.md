# Samsung TV Notify

Show Home Assistant notifications as native banners on a Samsung Tizen TV: the same small
pop-up the TV uses for its own messages, without taking over the screen.

It has two parts:

1. **HA Notify**, a small Tizen web app on the TV (`tv-app/`). Its background service listens
   on port 8099 and shows banners with `webapis.postPlainNotification`.
2. **The Home Assistant integration** (`custom_components/samsung_tv_notify`). It provides a
   `notify` entity, a "Notification service" sensor and a "Start notification service" button.

Tested on a Samsung S95C (2023, Tizen 9.0 firmware 2220) with Home Assistant 2026.10.

## Limitations

- **Text only.** Banners show a title and a message. Tizen's notification APIs that third-party
  apps can use on the TV do not render images: `tizen.notification` is an empty stub, and W3C
  notifications show the icon value as text.
- **Starting the service briefly shows the app.** A background service can only be started by
  launching its app, so the TV shows a dark "HA Notify service started" screen for about half a
  second. With *Start the service automatically* on (the default), this happens only when the
  service isn't running, typically after the TV has been off.
- **Developer mode.** The app is installed with Samsung's developer tools and a Samsung
  certificate bound to your TV.

## Install the TV app

You need: the TV in developer mode with your computer's IP as *Host PC IP*, Docker, and a
Samsung account.

1. **Developer mode.** On the TV open *Apps* and type `1 2 3 4 5` (use the on-screen number pad
   on remotes without number keys). Turn developer mode on, enter your computer's IP and restart
   the TV.
2. **Build the tool image.** It contains Samsung's `sdb` and [tizen.js](https://github.com/reisxd/tizen.js),
   which builds, signs and creates certificates without Tizen Studio:
   ```bash
   cd tv-app
   curl -sSLO https://download.tizen.org/sdk/tizenstudio/official/binary/sdb_4.2.36_ubuntu-64.zip
   unzip -p sdb_4.2.36_ubuntu-64.zip data/tools/sdb > sdb && chmod +x sdb
   git clone --depth 1 https://github.com/reisxd/tizen.js
   docker build -t tvnotify-tool .
   docker run -d --name tvnotify --net=host -v "$PWD":/work tvnotify-tool sleep infinity
   ```
3. **Connect and read the TV's DUID:**
   ```bash
   docker exec tvnotify sdb connect <TV-IP>:26101
   docker exec tvnotify sdb shell 0 getduid
   ```
4. **Create a Samsung certificate.** Sign in at
   <https://account.samsung.com/accounts/TDC/signInGate?clientId=v285zxnl3h&tokenType=TOKEN>,
   save the JSON the page shows as `samsung-login.json` and run:
   ```bash
   docker exec tvnotify node /work/scripts/create_cert.js /work/samsung-login.json <DUID> /work/cert/samsung
   ```
   The login token is only sent to Samsung's certificate server. Delete `samsung-login.json`
   afterwards.
5. **Install.** Push the device profile and run the deploy script with your TV's sdb address:
   ```bash
   docker exec tvnotify sdb shell 0 mkdir -p /home/owner/share/tmp/sdk_tools
   docker exec tvnotify sdb push /work/cert/samsung/device-profile.xml /home/owner/share/tmp/sdk_tools/device-profile.xml
   docker exec -e TV_SDB=<TV-IP>:26101 tvnotify /work/scripts/deploy.sh
   ```
   Check it: `curl http://<TV-IP>:8099/health` should return `{"ok":true}`.

## Install the integration

With HACS: add `https://github.com/LarsNorgaard/samsung-tv-notify` as a custom repository (category *Integration*), install
*Samsung TV Notify* and restart Home Assistant. Without HACS: copy
`custom_components/samsung_tv_notify` into your `config/custom_components/` and restart.

Then add it under **Settings → Devices & services → Add integration → Samsung TV Notify** and
enter the TV's IP address. The TV must be on; setup starts the app once.

## Use it

```yaml
action: notify.send_message
target:
  entity_id: notify.living_room_tv
data:
  title: Front door
  message: Someone is at the door
```

Options (**Configure** on the integration): *Start the service automatically* and *Banner
display time* (3–60 seconds, default 10).

## The service API

The TV app can also be used without Home Assistant:

- `GET http://<TV-IP>:8099/health` returns `{"ok": true}`.
- `POST http://<TV-IP>:8099/notify` with `{"title": "...", "message": "...", "timeout": 10}`
  shows a banner.
- `POST http://<TV-IP>:8001/api/v2/applications/HAnotifyPC.HANotify` (Samsung's own REST API)
  launches the app, which starts the service.

The service has no authentication: anything on your LAN can show a banner on the TV.

## Development

```bash
docker run --rm -v "$PWD":/src -w /src python:3.14-slim sh -c \
  'pip install -q pytest-homeassistant-custom-component ruff && ruff check . && python -m pytest -q'
```
