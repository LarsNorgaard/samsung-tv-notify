#!/bin/sh
# Build, sign, install and start HA Notify on the TV (runs inside the tool container).
# usage: TV_SDB=<TV-IP>:26101 deploy.sh   (the address you passed to "sdb connect")
set -e
S="-s ${TV_SDB:?set TV_SDB to the sdb address, e.g. 192.0.2.20:26101}"
P=$(cat /work/cert/samsung/password)
rm -f /work/build/HANotify.wgt
cd /work/app
tizenjs build . -t wgt -o /work/build/HANotify.wgt \
  --author /work/cert/samsung/author.p12 --authorPwd "$P" \
  --distributor /work/cert/samsung/distributor.p12 --distributorPwd "$P" >/dev/null
unzip -l /work/build/HANotify.wgt | tail -1
sdb $S push /work/build/HANotify.wgt /home/owner/share/tmp/sdk_tools/HANotify.wgt 2>&1 | tail -1
timeout 120 sdb $S shell 0 vd_appinstall HAnotifyPC.HANotify /home/owner/share/tmp/sdk_tools/HANotify.wgt 2>&1 | grep -E "completed|fail|error" || true
sleep 3
timeout 30 sdb $S shell 0 was_execute HAnotifyPC.HANotify 2>&1 | grep -E "launched|fail" || true
