import urllib.request, json, time, zipfile, io, os, subprocess

token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN') or subprocess.getoutput("git config --get user.token || true")
if not token:
    try:
        token = subprocess.check_output(["git", "remote", "get-url", "origin"], text=True).split("//")[1].split("@")[0].split(":")[1]
    except Exception:
        token = ""
run_id = '44061538406'
jobs_url = f'https://api.github.com/repos/boolforge/scummvm-snatcher/actions/runs/{run_id}/jobs'

print(f"Monitoring build {run_id}...")
for _ in range(50):
    time.sleep(10)
    req = urllib.request.Request(jobs_url, headers={'User-Agent': 'Mozilla/5.0', 'Authorization': f'Bearer {token}'})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            for j in data.get('jobs', []):
                if j['name'] == 'Build Android APK':
                    if j['status'] == 'completed' and j.get('conclusion') == 'success':
                        print("Build completed with success!")
                        break
            else:
                continue
            break
    except Exception as e:
        print("Polling error:", e)

# Download
art_url = f'https://api.github.com/repos/boolforge/scummvm-snatcher/actions/runs/{run_id}/artifacts'
req = urllib.request.Request(art_url, headers={'User-Agent': 'Mozilla/5.0', 'Authorization': f'Bearer {token}'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    for a in data.get('artifacts', []):
        if a['name'] == 'scummvm-snatcher-android-debug-apk':
            dl_url = a['archive_download_url']
            class NoAuthRedirectHandler(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return urllib.request.Request(newurl, headers={'User-Agent': 'Mozilla/5.0'}, method=req.get_method())
            opener = urllib.request.build_opener(NoAuthRedirectHandler)
            req2 = urllib.request.Request(dl_url, headers={'User-Agent': 'Mozilla/5.0', 'Authorization': f'Bearer {token}'})
            with opener.open(req2) as dl_resp:
                z = zipfile.ZipFile(io.BytesIO(dl_resp.read()))
                for fname in z.namelist():
                    if fname.endswith('.apk'):
                        out_path = '/storage/emulated/0/Download/ScummVM-Snatcher-Latest.apk'
                        with open(out_path, 'wb') as out_f:
                            out_f.write(z.read(fname))
                        cmd = 'cp /storage/emulated/0/Download/ScummVM-Snatcher-Latest.apk /data/local/tmp/scummvm.apk && chmod 644 /data/local/tmp/scummvm.apk && pm install -r /data/local/tmp/scummvm.apk && rm -f /data/local/tmp/scummvm.apk'
                        subprocess.run(['rish', '-c', cmd], check=True)
                        print("New APK cleanly reinstalled via Shizuku!")
                        exit(0)
