import os
import shutil
import json
import struct
import threading
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox

# --------------------------------------------------
#       Project Rebearth Mod Manager v1.0
#          by EatherBone for community <3
# --------------------------------------------------

CONFIG_FILE = "config.json"

# paths
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# js injection

MOD_LOADER_JS = """
(function() {
    console.log("Rebearth Mod Tools v3.3: Active");

    const style = document.createElement('style');
    style.textContent = `
        #rebearth-mod-panel {
            position: fixed; top: 15px; left: 15px; z-index: 999999;
            background: #e8daa8; border: 3px solid #562c1b; padding: 10px;
            font-family: 'Lato', sans-serif; color: #562c1b;
            display: flex; flex-direction: column; gap: 8px;
            min-width: 200px; box-shadow: 0 5px 25px rgba(0,0,0,0.7);
            pointer-events: auto; transition: transform 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28);
        }
        
        #rebearth-mod-panel.collapsed { 
            transform: translateX(-245px); 
        }

        #rebearth-mod-toggle {
            position: absolute; right: -55px; top: 50%;
            transform: translateY(-50%);
            background: #562c1b; color: #e8daa8;
            padding: 8px 12px; border: 2px solid #ebb933; border-left: none;
            border-radius: 0 10px 10px 0; cursor: pointer;
            font-weight: bold; font-size: 12px;
            display: none; box-shadow: 5px 0 10px rgba(0,0,0,0.3);
        }
        #rebearth-mod-panel.collapsed #rebearth-mod-toggle { display: block; }

        .mod-header { font-weight: 800; font-size: 14px; border-bottom: 2px solid #562c1b; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center; }
        .mod-section { font-size: 10px; font-weight: bold; margin-top: 5px; text-transform: uppercase; opacity: 0.8; }
        .mod-btn { background-color: #562c1b; color: #e8daa8; border: 1px solid #ebb933; padding: 6px; cursor: pointer; font-weight: bold; font-size: 10px; text-transform: uppercase; text-align: center; transition: 0.1s; }
        .mod-btn:hover { background: #ebb933; color: #562c1b; }
        .mod-btn.active { background: #4caf50; color: white; border-color: #fff; }
        
        .ui-hidden-mod { display: none !important; }
        .ui-ghost-mod { opacity: 0.15 !important; pointer-events: none !important; transition: opacity 0.5s ease; }
        
        .cinema-bar { position: fixed; left: 0; width: 100%; height: 0; background: black; z-index: 999998; transition: height 0.5s ease; pointer-events: none; }
        .cinema-active .cinema-bar { height: 12%; }
        
        .enhanced-visuals { filter: contrast(1.15) saturate(1.2) brightness(1.05) !important; }
        .golden-hour { filter: sepia(0.3) saturate(1.4) hue-rotate(-10deg) brightness(1.05) !important; }
        .deep-night { filter: brightness(0.5) contrast(1.3) hue-rotate(185deg) saturate(0.7) !important; }
        
        #fps-display { font-family: monospace; font-size: 12px; font-weight: bold; color: #562c1b; background: rgba(0,0,0,0.05); padding: 2px 5px; border-radius: 3px; }
    `;
    document.head.appendChild(style);

    const topBar = document.createElement('div'); topBar.className = 'cinema-bar'; topBar.style.top = '0';
    const botBar = document.createElement('div'); botBar.className = 'cinema-bar'; botBar.style.bottom = '0';
    document.body.appendChild(topBar); document.body.appendChild(botBar);

    const panel = document.createElement('div');
    panel.id = 'rebearth-mod-panel';
    panel.innerHTML = `
        <div class="mod-header">
            <span>RebearthTools v1.0</span>
            <div id="fps-display">FPS: --</div>
        </div>
        
        <div class="mod-section">Visibility</div>
        <button class="mod-btn" id="btn-hide-ui">Full Hide (H)</button>
        <button class="mod-btn" id="btn-zen-ui">Zen Focus (F)</button>
        <button class="mod-btn" id="btn-ghost-ui">Ghost HUD (T)</button>
        
        <div class="mod-section">Atmosphere</div>
        <button class="mod-btn" id="btn-cinema">Cinema Bars (C)</button>
        <button class="mod-btn" id="btn-enhance">Vivid View (V)</button>
        <button class="mod-btn" id="btn-golden">Golden Hour (G)</button>
        <button class="mod-btn" id="btn-night">Deep Night (N)</button>
        
        <div style="font-size: 8px; opacity: 0.5; margin-top: 5px; text-align: center;">M - Collapse Menu</div>
        <div id="rebearth-mod-toggle">MODS ▶</div>
    `;
    document.body.appendChild(panel);

    // functions
    const allUI = ['#hud_wrapper', '#stats_wrapper', '#menu', '#minimap', '#issues-button', '#name_box'];
    const nonCriticalUI = ['#stats_wrapper', '#menu', '#minimap', '#issues-button', '#name_box'];
    
    function resetUI() { allUI.forEach(s => document.querySelector(s)?.classList.remove('ui-hidden-mod', 'ui-ghost-mod')); }
    
    function updateBtnStates() {
        const hud = document.querySelector('#hud_wrapper');
        document.getElementById('btn-hide-ui').classList.toggle('active', hud?.classList.contains('ui-hidden-mod'));
        document.getElementById('btn-zen-ui').classList.toggle('active', !hud?.classList.contains('ui-hidden-mod') && document.querySelector('#menu')?.classList.contains('ui-hidden-mod'));
        document.getElementById('btn-ghost-ui').classList.toggle('active', hud?.classList.contains('ui-ghost-mod'));
    }

    document.getElementById('btn-hide-ui').onclick = () => { 
        const isH = document.querySelector('#hud_wrapper').classList.contains('ui-hidden-mod');
        resetUI(); if(!isH) allUI.forEach(s => document.querySelector(s)?.classList.add('ui-hidden-mod'));
        updateBtnStates();
    };

    document.getElementById('btn-zen-ui').onclick = () => {
        const isZ = document.querySelector('#menu').classList.contains('ui-hidden-mod');
        resetUI(); if(!isZ) nonCriticalUI.forEach(s => document.querySelector(s)?.classList.add('ui-hidden-mod'));
        updateBtnStates();
    };

    document.getElementById('btn-ghost-ui').onclick = () => {
        const isG = document.querySelector('#hud_wrapper').classList.contains('ui-ghost-mod');
        resetUI(); if(!isG) allUI.forEach(s => document.querySelector(s)?.classList.add('ui-ghost-mod'));
        updateBtnStates();
    };

    document.getElementById('btn-cinema').onclick = () => {
        document.body.classList.toggle('cinema-active');
        document.getElementById('btn-cinema').classList.toggle('active', document.body.classList.contains('cinema-active'));
    };

    const applyFilter = (cls, btnId) => {
        const g = document.querySelector('#game');
        const btn = document.getElementById(btnId);
        const active = g.classList.contains(cls);
        g.classList.remove('enhanced-visuals', 'golden-hour', 'deep-night');
        document.querySelectorAll('.mod-section + .mod-btn, .mod-btn[id^="btn-"]').forEach(b => { if(b.id.includes('enhance') || b.id.includes('golden') || b.id.includes('night')) b.classList.remove('active'); });
        if(!active) { g.classList.add(cls); btn.classList.add('active'); }
    };

    document.getElementById('btn-enhance').onclick = () => applyFilter('enhanced-visuals', 'btn-enhance');
    document.getElementById('btn-golden').onclick = () => applyFilter('golden-hour', 'btn-golden');
    document.getElementById('btn-night').onclick = () => applyFilter('deep-night', 'btn-night');

    const togglePanel = () => panel.classList.toggle('collapsed');
    document.getElementById('rebearth-mod-toggle').onclick = togglePanel;

    // fps counter
    let times = [];
    let fpsDisplay = document.getElementById('fps-display');

    function refreshFPS() {
        window.requestAnimationFrame(() => {
            const now = performance.now();
            while (times.length > 0 && times[0] <= now - 1000) {
                times.shift();
            }
            times.push(now);
            const fps = times.length;
            if (fpsDisplay) fpsDisplay.innerText = "FPS: " + fps;
            refreshFPS();
        });
    }
    refreshFPS();

    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (e.code === 'KeyH') document.getElementById('btn-hide-ui').click();
        if (e.code === 'KeyF') document.getElementById('btn-zen-ui').click();
        if (e.code === 'KeyT') document.getElementById('btn-ghost-ui').click();
        if (e.code === 'KeyC') document.getElementById('btn-cinema').click();
        if (e.code === 'KeyV') document.getElementById('btn-enhance').click();
        if (e.code === 'KeyG') document.getElementById('btn-golden').click();
        if (e.code === 'KeyN') document.getElementById('btn-night').click();
        if (e.code === 'KeyM') togglePanel();
    });
})();
"""

class AsarTool:
    @staticmethod
    def extract(asar_path, out_dir):
        with open(asar_path, 'rb') as f:
            f.seek(12)
            header_size = struct.unpack('<I', f.read(4))[0]
            header_json = f.read(header_size).decode('utf-8')
            header = json.loads(header_json[:header_json.rfind('}')+1])
            base_offset = 16 + ((header_size + 3) & ~3)
            def collect(files, rel_parts=[]):
                for name, info in files.items():
                    curr = rel_parts + [name]
                    if 'files' in info: collect(info['files'], curr)
                    else:
                        if 'offset' not in info: continue
                        full_p = os.path.join(out_dir, *curr)
                        os.makedirs(os.path.dirname(full_p), exist_ok=True)
                        f.seek(base_offset + int(info['offset']))
                        with open(full_p, 'wb') as out:
                            rem = int(info['size'])
                            while rem > 0:
                                chunk = f.read(min(rem, 1024*1024))
                                if not chunk: break
                                out.write(chunk); rem -= len(chunk)
            collect(header['files'])

class ModManagerApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Project Rebearth Mod Manager v1.0")
        self.geometry("600x520")
        
        # copy assets
        self.ensure_assets_on_disk()
        
        # icon
        try:
            self.iconbitmap(os.path.join("assets", "icon.ico"))
        except: pass

        self.game_path = ""
        self.setup_ui()
        self.load_config()

    def ensure_assets_on_disk(self):
        local_assets_dir = os.path.join(os.getcwd(), "assets")
        if not os.path.exists(local_assets_dir):
            os.makedirs(local_assets_dir)
        
        files_to_extract = ["project_rebearth.exe", "icon.ico"]
        for filename in files_to_extract:
            target_path = os.path.join(local_assets_dir, filename)
            # no exe in assets? Ok - we take ours from tools exe
            if not os.path.exists(target_path):
                try:
                    src = resource_path(os.path.join("assets", filename))
                    if os.path.exists(src):
                        shutil.copy2(src, target_path)
                except Exception as e:
                    print(f"Extraction error: {e}")

    def setup_ui(self):
        ctk.CTkLabel(self, text="REBEARTH TOOLS v1.0", font=("Arial", 22, "bold")).pack(pady=20)
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(pady=10, padx=30, fill="x")
        self.lbl_status = ctk.CTkLabel(self.status_frame, text="STATUS: INITIALIZING", font=("Arial", 13, "bold"))
        self.lbl_status.pack(pady=15)

        ctk.CTkButton(self, text="1. SELECT GAME FOLDER", command=self.browse_game).pack(pady=10)
        self.btn_install = ctk.CTkButton(self, text="2. INSTALL MOD PANEL", fg_color="green", command=self.install_mods)
        self.btn_install.pack(pady=10)
        self.btn_uninstall = ctk.CTkButton(self, text="3. UNINSTALL MODS (RESTORE)", fg_color="#c0392b", command=self.uninstall_mods)
        self.btn_uninstall.pack(pady=10)
        ctk.CTkButton(self, text="LAUNCH GAME", fg_color="#27ae60", command=self.launch_game, height=40).pack(pady=20)

    def browse_game(self):
        path = filedialog.askdirectory()
        if path:
            self.game_path = path
            self.update_state()
            with open(CONFIG_FILE, "w") as f: json.dump({"game_path": self.game_path}, f)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    self.game_path = json.load(f).get("game_path", "")
                    if os.path.exists(self.game_path): self.update_state()
            except: pass

    def update_state(self):
        if not self.game_path: return
        self.res_path = os.path.join(self.game_path, "resources")
        self.app_folder = os.path.join(self.res_path, "app")
        if os.path.exists(self.app_folder) and not os.path.exists(os.path.join(self.res_path, "app.asar")):
            self.lbl_status.configure(text="MODS ACTIVE", text_color="green")
            self.btn_install.configure(state="disabled")
            self.btn_uninstall.configure(state="normal")
        else:
            self.lbl_status.configure(text="CLEAN VERSION", text_color="#3498db")
            self.btn_install.configure(state="normal")
            self.btn_uninstall.configure(state="disabled")

    def patch_exe(self):
        src = os.path.join(os.getcwd(), "assets", "project_rebearth.exe")
        dst = os.path.join(self.game_path, "project_rebearth.exe")
        if os.path.exists(src):
            try: shutil.copy2(src, dst); return True
            except: return False
        return False

    def install_mods(self):
        asar_p = os.path.join(self.res_path, "app.asar")
        unp_p = os.path.join(self.res_path, "app.asar.unpacked")
        if not os.path.exists(asar_p): return messagebox.showerror("Error", "app.asar not found!")

        def run():
            try:
                AsarTool.extract(asar_p, self.app_folder)
                if os.path.exists(unp_p):
                    for root, _, files in os.walk(unp_p):
                        rel = os.path.relpath(root, unp_p)
                        dest = os.path.join(self.app_folder, rel)
                        os.makedirs(dest, exist_ok=True)
                        for f in files: shutil.copy2(os.path.join(root, f), os.path.join(dest, f))
                
                self.patch_exe()

                html = os.path.join(self.app_folder, "dist", "game.html")
                js = os.path.join(self.app_folder, "dist", "mod-loader.js")
                with open(js, "w", encoding="utf-8") as f: f.write(MOD_LOADER_JS)
                with open(html, "r", encoding="utf-8") as f: content = f.read()
                if "mod-loader.js" not in content:
                    with open(html, "w", encoding="utf-8") as f:
                        f.write(content.replace("</body>", '<script src="mod-loader.js"></script></body>'))
                
                b_dir = os.path.join(self.res_path, "_backups")
                os.makedirs(b_dir, exist_ok=True)
                shutil.move(asar_p, os.path.join(b_dir, "app.asar"))
                if os.path.exists(unp_p): shutil.move(unp_p, os.path.join(b_dir, "app.asar.unpacked"))
                
                self.after(0, lambda: [self.update_state(), messagebox.showinfo("Success", "Mods Installed! <3")])
            except Exception as e:
                msg = str(e)
                self.after(0, lambda m=msg: messagebox.showerror("Error", f"Failed: {m}"))

        threading.Thread(target=run, daemon=True).start()

    def uninstall_mods(self):
        b_asar = os.path.join(self.res_path, "_backups", "app.asar")
        b_unp = os.path.join(self.res_path, "_backups", "app.asar.unpacked")
        if not os.path.exists(b_asar): return messagebox.showerror("Error", "Backup not found!")
        try:
            if os.path.exists(self.app_folder): shutil.rmtree(self.app_folder)
            shutil.move(b_asar, os.path.join(self.res_path, "app.asar"))
            if os.path.exists(b_unp): shutil.move(b_unp, os.path.join(self.res_path, "app.asar.unpacked"))
            if os.path.exists(os.path.join(self.res_path, "_backups")): shutil.rmtree(os.path.join(self.res_path, "_backups"))
            self.update_state()
            messagebox.showinfo("Done", "Restored to vanilla!")
        except Exception as e: messagebox.showerror("Error", str(e))

    def launch_game(self):
        exe = os.path.join(self.game_path, "project_rebearth.exe")
        if os.path.exists(exe): os.startfile(exe)

if __name__ == "__main__":
    ModManagerApp().mainloop()