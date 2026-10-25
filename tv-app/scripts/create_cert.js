// Create a Samsung author+distributor certificate for the TV from a Samsung
// sign-in JSON (https://account.samsung.com/accounts/TDC/signInGate?clientId=v285zxnl3h&tokenType=TOKEN).
// usage: node create_cert.js <login.json> <duid> <outdir>
const { SamsungCertificateCreator } = require('/opt/tizen.js');
const { readFileSync, writeFileSync, mkdirSync } = require('fs');
const crypto = require('crypto');

(async () => {
    const [loginPath, duid, outDir] = process.argv.slice(2);
    const login = JSON.parse(readFileSync(loginPath, 'utf8'));
    const accessInfo = { accessToken: login.access_token, userId: login.userId };
    if (!accessInfo.accessToken || !accessInfo.userId) throw new Error('login JSON lacks access_token/userId');

    const password = crypto.randomBytes(18).toString('base64url');
    const authorInfo = {
        name: 'HANotify',
        email: login.inputEmailID,
        password,
        privilegeLevel: 'Partner'
    };

    const cert = await new SamsungCertificateCreator().createCertificate(authorInfo, accessInfo, [duid]);
    mkdirSync(outDir, { recursive: true, mode: 0o700 });
    writeFileSync(`${outDir}/author.p12`, cert.authorCert, { encoding: 'binary', mode: 0o600 });
    writeFileSync(`${outDir}/distributor.p12`, cert.distributorCert, { encoding: 'binary', mode: 0o600 });
    writeFileSync(`${outDir}/device-profile.xml`, cert.distributorXML, { mode: 0o600 });
    writeFileSync(`${outDir}/password`, password, { mode: 0o600 });
    console.log('certificate created in', outDir);
})().catch(e => { console.error('ERROR:', e.message); process.exit(1); });
