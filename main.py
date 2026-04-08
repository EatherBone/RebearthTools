import os
import shutil
import json
import struct
import threading
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox

# --------------------------------------------------
#       Project Rebearth Mod Manager v1.2
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
        self.title("Project Rebearth Mod Manager v1.2")
        self.geometry("620x560")
        
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
            if not os.path.exists(target_path):
                try:
                    src = resource_path(os.path.join("assets", filename))
                    if os.path.exists(src):
                        shutil.copy2(src, target_path)
                except Exception as e:
                    print(f"Extraction error: {e}")

    def setup_ui(self):
        ctk.CTkLabel(self, text="REBEARTH TOOLS v1.2", font=("Arial", 22, "bold")).pack(pady=15)
        
        # status
        self.status_frame = ctk.CTkFrame(self)
        self.status_frame.pack(pady=5, padx=30, fill="x")
        self.lbl_status = ctk.CTkLabel(self.status_frame, text="STATUS: Select game folder", font=("Arial", 12, "bold"))
        self.lbl_status.pack(pady=10)
        
        # a lil laber unda the satus
        ctk.CTkLabel(self, text="This program make backups but anyway use it at your own risk <3 ", 
                    font=("Arial", 10), text_color="#666").pack(pady=2)
        
        # btns
        ctk.CTkButton(self, text="Info", command=self.show_calc_info, 
                     fg_color="#ebb933", text_color="#562c1b").pack(pady=5)
        
        ctk.CTkButton(self, text="1. SELECT GAME FOLDER", command=self.browse_game).pack(pady=8)
        
        self.btn_install = ctk.CTkButton(self, text="2. INSTALL MODS", fg_color="green", command=self.install_mods)
        self.btn_install.pack(pady=8)
        
        self.btn_uninstall = ctk.CTkButton(self, text="3. UNINSTALL MODS (RESTORE)", fg_color="#c0392b", command=self.uninstall_mods)
        self.btn_uninstall.pack(pady=8)
        
        ctk.CTkButton(self, text="LAUNCH GAME", fg_color="#27ae60", command=self.launch_game, height=40, font=("Arial", 12, "bold")).pack(pady=15)
        
        # footer
        ctk.CTkLabel(self, text="by EatherBone • Tools • Calculator", font=("Arial", 9), text_color="#888").pack(side="bottom", pady=5)

    def show_calc_info(self):
        messagebox.showinfo("Info", 
                          "In-game buttons and hotkeys!\n\n"
                          "After installing mods:\n"
                          "1. Launch Project Rebearth\n"
                          "2. Press 'M' to open or hide mods menu\n")

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
            self.lbl_status.configure(text="✅ MODS ACTIVE", text_color="green")
            self.btn_install.configure(state="disabled")
            self.btn_uninstall.configure(state="normal")
        else:
            self.lbl_status.configure(text="⚪ CLEAN VERSION", text_color="#3498db")
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
                
                self.after(0, lambda: [self.update_state(), messagebox.showinfo("Success", "Mods Installed! <3\n\n")])
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

#  MAIN JS LOGIC. Injecting this stuff to the game as mods


MOD_LOADER_JS = """
(function() {
console.log("=RT= Rebearth Tools v1.2");

// main config

const RECIPES = {
    'Wood': { produced_by: 'Woodcutter', output: {'Wood': 30, 'Stone': 15, 'Earth': 5, 'Arctic': 0}, inputs: {}, inputs_biome: {'Wood': {'Tools': 0.05}}, population: 4, construction: {'Wood': {'Wood': 50}, 'Stone': {'Wood': 50}, 'Earth': {'Wood': 50}, 'Arctic': {'Wood': 50}}, note: 'Not in Arctic' },
    'Stone': { produced_by: 'Quarry + Stone Crane', output: {'Wood': 20, 'Stone': 30, 'Earth': 10, 'Arctic': 0}, inputs: {}, population: 2, construction: {'Wood': {'Wood': 60}, 'Stone': {'Stone': 60}, 'Earth': {'Earth': 60}, 'Arctic': {'Wood': 60}}, note: 'Stone Crane /day' },
    'Earth': { produced_by: 'Claypit + Clay Crane', output: {'Wood': 20, 'Stone': 10, 'Earth': 30, 'Arctic': 0}, inputs: {}, population: 2, construction: {'Wood': {'Wood': 60}, 'Stone': {'Stone': 60}, 'Earth': {'Earth': 60}, 'Arctic': {'Wood': 60}}, note: 'Clay Crane /day' },
    'Ore': { produced_by: 'Iron Mine', output: {'Wood': 40, 'Stone': 100, 'Earth': 60, 'Arctic': 0}, inputs: {}, population: 50, construction: {'Wood': {'Wood': 50}, 'Stone': {'Stone': 50}, 'Earth': {'Earth': 50}, 'Arctic': {'Wood': 50}}, note: 'Not in Arctic' },
    // processing buildings
    'Grain': { produced_by: 'Field', output: {'Wood': 100, 'Stone': 100, 'Earth': 100, 'Arctic': 100}, inputs: {}, population: 10, construction: {'Wood': {'Wood': 2}, 'Stone': {'Stone': 2}, 'Earth': {'Earth': 2}, 'Arctic': {'Wood': 2}} },
    'Wool':  { produced_by: 'Sheep Field', output: {'Wood': 50, 'Stone': 50, 'Earth': 50, 'Arctic': 50}, inputs: {}, population: 0, construction: {'Wood': {'Wood': 2}, 'Stone': {'Stone': 2}, 'Earth': {'Earth': 2}, 'Arctic': {'Wood': 2}}, note: 'per 10000m²' },
    'Milk':  { produced_by: 'Cow/Goat Field', output: {'Wood': 50, 'Stone': 50, 'Earth': 50, 'Arctic': 50}, inputs: {}, population: 0, construction: {'Wood': {'Wood': 2}, 'Stone': {'Stone': 2}, 'Earth': {'Earth': 2}, 'Arctic': {'Wood': 2}}, note: 'per 10000m²' },
    'Flour': { produced_by: 'Windmill', output: {'Wood': 100, 'Stone': 100, 'Earth': 100, 'Arctic': 100}, inputs: { 'Grain': 100 }, population: 5, construction: {'Wood': {'Wood': 30, 'Stone': 20, 'Tools': 1}, 'Stone': {'Wood': 30, 'Stone': 20, 'Tools': 1}, 'Earth': {'Wood': 30, 'Stone': 20, 'Tools': 1}, 'Arctic': {'Wood': 30, 'Stone': 20, 'Tools': 1}} },
    'Metal': { produced_by: 'Refinery', output: {'Wood': 10, 'Stone': 10, 'Earth': 10, 'Arctic': 10}, inputs: { 'Ore': 50 }, population: 20, construction: {'Wood': {'Wood': 100, 'Stone': 200, 'Tools': 10}, 'Stone': {'Wood': 50, 'Stone': 300, 'Tools': 10}, 'Earth': {'Stone': 100, 'Earth': 200, 'Tools': 10}, 'Arctic': {'Wood': 100, 'Stone': 200, 'Tools': 10}} },
    'Glass': { produced_by: 'Glassworks', output: {'Wood': 5, 'Stone': 5, 'Earth': 5, 'Arctic': 0}, inputs: { 'Earth': 50 }, population: 10, construction: {'Wood': {'Wood': 100, 'Metal': 10, 'Tools': 10}, 'Stone': {'Stone': 100, 'Metal': 10, 'Tools': 10}, 'Earth': {'Earth': 100, 'Metal': 10, 'Tools': 10}}, note: 'Not in Arctic' },
    'Tools': { produced_by: 'Tools Workshop', output: {'Wood': 2, 'Stone': 2, 'Earth': 2, 'Arctic': 2}, inputs: { 'Metal': 4, 'Wood': 5 }, population: 10, construction: {'Wood': {'Wood': 50}, 'Stone': {'Stone': 50}, 'Earth': {'Earth': 50}, 'Arctic': {'Wood': 50}} },
    'Clothes': { produced_by: 'Tailor', output: {'Wood': 50, 'Stone': 50, 'Earth': 50, 'Arctic': 50}, inputs: { 'Wool': 50 }, population: 10, construction: {'Wood': {'Wood': 50}, 'Stone': {'Stone': 50}, 'Earth': {'Earth': 50}, 'Arctic': {'Wood': 50}} },
    'Drinks': { produced_by: 'Brewery', output: {'Wood': 50, 'Stone': 50, 'Earth': 50, 'Arctic': 50}, inputs: { 'Grain': 50 }, population: 10, construction: {'Wood': {'Wood': 50}, 'Stone': {'Stone': 50}, 'Earth': {'Earth': 50}, 'Arctic': {'Wood': 50}} },
    'Food':   { produced_by: 'Bakery', output: {'Wood': 100, 'Stone': 100, 'Earth': 100, 'Arctic': 100}, inputs: { 'Flour': 50 }, population: 4, construction: {'Wood': {'Wood': 100, 'Stone': 50, 'Tools': 5}, 'Stone': {'Wood': 100, 'Stone': 50, 'Tools': 5}, 'Earth': {'Wood': 50, 'Stone': 100, 'Tools': 5}, 'Arctic': {'Wood': 100, 'Stone': 50, 'Tools': 5}} },
    'Coin':   { produced_by: 'Tavern', output: {'Wood': 10, 'Stone': 10, 'Earth': 10, 'Arctic': 10}, inputs: { 'Drinks': 10 }, population: 5, construction: {'Wood': {'Wood': 50}, 'Stone': {'Stone': 50}, 'Earth': {'Earth': 50}, 'Arctic': {'Wood': 50}} },
    'Cream':  { produced_by: 'Creamery', output: {'Wood': 50, 'Stone': 50, 'Earth': 50, 'Arctic': 50}, inputs: { 'Milk': 50 }, population: 5, construction: {'Wood': {'Wood': 50}, 'Stone': {'Stone': 50}, 'Earth': {'Earth': 50}, 'Arctic': {'Wood': 50}} }
};
const ALL_RESOURCES = Object.keys(RECIPES);
const BIOMES = {
    'Wood':   { name: 'Wood Biome',   primaryResource: 'Wood',  housingUpkeep: 1.0, constructionCost: 1.0, description: 'Forest — best Wood, Tools cost on Woodcutter', color: '#2d5016' },
    'Stone':  { name: 'Stone Biome',  primaryResource: 'Stone', housingUpkeep: 1.0, constructionCost: 1.0, description: 'Mountains — best Ore (100/day) & Stone', color: '#5a5a5a' },
    'Earth':  { name: 'Earth Biome',  primaryResource: 'Earth', housingUpkeep: 0.1, constructionCost: 1.0, description: 'Arid — best Earth, ×0.1 Wood upkeep', color: '#8b7355' }
    // 'Arctic': { name: 'Arctic Biome', primaryResource: 'None',  housingUpkeep: 2.0, constructionCost: 2.0, description: 'Frozen — no extraction, ×2 Wood upkeep', color: '#a8d8ea' }
};
const ALL_BIOMES = Object.keys(BIOMES);

// css compressed af so gl
const style = document.createElement('style');
style.textContent = `
    #rebearth-mod-panel {
    position: fixed; top: 15px; left: 15px; z-index: 999999;
    background: #e8daa8; border: 3px solid #562c1b; padding: 10px;
    font-family: 'Lato', sans-serif; color: #562c1b;
    display: flex; flex-direction: column; gap: 8px;
    min-width: 300px;
    box-shadow: 0 5px 25px rgba(0,0,0,0.7);
    pointer-events: auto; transition: transform 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28);
    max-height: 90vh; 
    overflow-y: auto; 
    overflow-x: hidden;
    }
    #rebearth-mod-panel.collapsed { transform: translateX(-360px); }
    #rebearth-mod-toggle { position: absolute; right: -60px; top: 50%; transform: translateY(-50%); background: #562c1b; color: #e8daa8; padding: 8px 12px; border: 2px solid #ebb933; border-left: none; border-radius: 0 10px 10px 0; cursor: pointer; font-weight: bold; font-size: 12px; display: none; box-shadow: 5px 0 10px rgba(0,0,0,0.3); }
    #rebearth-mod-panel.collapsed #rebearth-mod-toggle { display: block; }
    .mod-header { font-weight: 800; font-size: 14px; border-bottom: 2px solid #562c1b; margin-bottom: 5px; display: flex; justify-content: space-between; align-items: center; }
    .mod-section { font-size: 10px; font-weight: bold; margin-top: 5px; text-transform: uppercase; opacity: 0.8; border-top: 1px dashed #562c1b; padding-top: 4px;}
    .mod-btn { background-color: #562c1b; color: #e8daa8; border: 1px solid #ebb933; padding: 6px; cursor: pointer; font-weight: bold; font-size: 10px; text-transform: uppercase; text-align: center; transition: 0.1s; width: 100%; }
    .mod-btn:hover { background: #ebb933; color: #562c1b; }
    .mod-btn.active { background: #4caf50; color: white; border-color: #fff; }
    .ui-hidden-mod { display: none !important; }
    .ui-ghost-mod { opacity: 0.15 !important; pointer-events: none !important; transition: opacity 0.5s ease; }
    .cinema-bar { position: fixed; left: 0; width: 100%; height: 0; background: black; z-index: 999998; transition: height 0.5s ease; pointer-events: none; }
    .cinema-active .cinema-bar { height: 10%; }
    .enhanced-visuals { filter: contrast(1.15) saturate(1.2) brightness(1.05) !important; }
    .golden-hour { filter: sepia(0.3) saturate(1.4) hue-rotate(-10deg) brightness(1.05) !important; }
    .deep-night { filter: brightness(0.6) contrast(1.2) hue-rotate(185deg) saturate(0.8) !important; }
    #fps-display { font-family: monospace; font-size: 11px; font-weight: bold; color: #562c1b; background: rgba(0,0,0,0.05); padding: 2px 5px; border-radius: 3px; }
    input[type=range] { width: 100%; accent-color: #562c1b; margin-top: 2px; }
    .slider-label { font-size: 9px; display: flex; justify-content: space-between; }
    
    /* calc styles */
    #calc-panel { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%) scale(0.95); background: #fff8e1; border: 4px solid #562c1b; border-radius: 8px; padding: 15px; min-width: 600px; max-width: 90vw; max-height: 85vh; font-family: 'Lato', sans-serif; color: #562c1b; z-index: 1000000; box-shadow: 0 10px 40px rgba(0,0,0,0.5); display: none; flex-direction: column; gap: 10px; opacity: 0; transition: all 0.25s ease; overflow-y: auto; }
    #calc-panel.visible { display: flex; transform: translate(-50%, -50%) scale(1); opacity: 1; }
    #calc-panel::before { content: ''; position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.4); z-index: -1; }
    .calc-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #562c1b; padding-bottom: 8px; margin-bottom: 5px; }
    .calc-header h3 { margin: 0; font-size: 16px; }
    .calc-close { background: #c0392b; color: white; border: none; padding: 4px 12px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 14px; }
    .calc-close:hover { background: #e74c3c; }
    .calc-inputs { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-bottom: 10px; }
    .calc-inputs label { font-size: 11px; font-weight: bold; display: flex; flex-direction: column; gap: 3px; }
    .calc-inputs select, .calc-inputs input { padding: 6px; border: 2px solid #562c1b; border-radius: 4px; background: #e8daa8; font-size: 12px; }
    .calc-inputs select:focus, .calc-inputs input:focus { outline: none; border-color: #ebb933; }
    .calc-btn { background: #562c1b; color: #e8daa8; border: none; padding: 8px; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 12px; transition: 0.15s; }
    .calc-btn:hover { background: #ebb933; color: #562c1b; }
    
    /* results */
    .calc-results { background: #f5ecd6; border: 1px solid #d4c494; border-radius: 4px; padding: 10px; max-height: 450px; overflow-y: auto; font-size: 11px; }
    .calc-results h4 { margin: 0 0 8px 0; font-size: 12px; border-bottom: 1px solid #d4c494; padding-bottom: 4px; }
    .calc-row { display: flex; justify-content: space-between; padding: 3px 0; border-bottom: 1px dashed #e8daa8; }
    .calc-row:last-child { border-bottom: none; }
    .calc-row.target { font-weight: bold; color: #c0392b; }
    .calc-row.producer { font-size: 10px; color: #666; font-style: italic; }
    .calc-row.building { background: #e8daa8; padding: 4px 8px; border-radius: 4px; margin: 2px 0; font-weight: bold; }
    .calc-row.building span:last-child { color: #c0392b; }
    .calc-row.population { background: #d4c494; padding: 4px 8px; border-radius: 4px; margin: 2px 0; }
    .calc-row.population span:last-child { color: #562c1b; font-weight: bold; }
    .calc-row.construction { background: #c4b594; padding: 4px 8px; border-radius: 4px; margin: 2px 0; font-size: 10px; }
    .calc-row.construction span:last-child { color: #562c1b; font-weight: 600; }
    
    /* chain visuals */
    .chain-node { margin: 4px 0; padding: 4px 8px; border-radius: 4px; background: rgba(255,255,255,0.6); border-left: 3px solid #562c1b; }
    .chain-node.level-0 { border-left-color: #c0392b; background: #fff; font-weight: bold; }
    .chain-node.level-1 { margin-left: 15px; border-left-color: #e67e22; }
    .chain-node.level-2 { margin-left: 30px; border-left-color: #f1c40f; }
    .chain-node.level-3 { margin-left: 45px; border-left-color: #27ae60; }
    .chain-node.level-4 { margin-left: 60px; border-left-color: #2980b9; }
    .chain-header { display: flex; justify-content: space-between; font-weight: 600; }
    .chain-details { font-size: 9px; color: #666; margin-top: 2px; display: flex; gap: 10px; }
    .chain-arrow { color: #562c1b; font-weight: bold; margin: 2px 0; opacity: 0.5; font-size: 10px; }
    
    .calc-summary { background: #562c1b; color: #e8daa8; padding: 10px; border-radius: 4px; margin-top: 10px; font-weight: bold; }
    .summary-row { display: flex; justify-content: space-between; margin: 3px 0; }
    .summary-row.total { border-top: 1px solid #ebb933; padding-top: 5px; margin-top: 5px; font-size: 13px; color: #ebb933; }
    .biome-info { font-size: 10px; padding: 5px 8px; border-radius: 4px; margin-top: 2px; font-weight: 500; color: #562c1b; }
    .calc-footer { font-size: 9px; opacity: 0.7; text-align: center; margin-top: 5px; }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #e8daa8; border-radius: 4px; }
    ::-webkit-scrollbar-thumb { background: #562c1b; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #ebb933; }
`;
document.head.appendChild(style);

// ui
const topBar = document.createElement('div'); topBar.className = 'cinema-bar'; topBar.style.top = '0';
const botBar = document.createElement('div'); botBar.className = 'cinema-bar'; botBar.style.bottom = '0';
document.body.appendChild(topBar); document.body.appendChild(botBar);

const panel = document.createElement('div');
panel.id = 'rebearth-mod-panel';
panel.innerHTML = `
    <div class="mod-header"><span>RebearthTools v1.2</span><div id="fps-display">FPS: --</div></div>
    <div class="mod-section">Visibility</div>
    <button class="mod-btn" id="btn-hide-ui">Full Hide (H)</button>
    <button class="mod-btn" id="btn-zen-ui">Zen Focus (F)</button>
    <button class="mod-btn" id="btn-ghost-ui">Ghost HUD (T)</button>
    <div class="mod-section">Atmosphere</div>
    <button class="mod-btn" id="btn-cinema">Cinema Bars (L)</button>
    <button class="mod-btn" id="btn-enhance">Vivid View (V)</button>
    <button class="mod-btn" id="btn-golden">Golden Hour (G)</button>
    <button class="mod-btn" id="btn-night">Deep Night (N)</button>
    <div class="mod-section">Tools</div>
    <button class="mod-btn" id="btn-calc" style="background:#ebb933; color:#562c1b;">Smart Calculator (C)</button>
    <div style="font-size: 8px; opacity: 1; margin-top: 5px; text-align: center;">M - Collapse Menu</div>
    <div id="rebearth-mod-toggle">MODS ▶</div>
`;
document.body.appendChild(panel);

// calc panel
const calcPanel = document.createElement('div');
calcPanel.id = 'calc-panel';
calcPanel.innerHTML = `
    <div class="calc-header">
        <h3>Production Chain Calculator</h3>
        <button class="calc-close" id="calc-close">✕ Close (Esc)</button>
    </div>
    <div class="calc-inputs">
        <label>Target Resource:
            <select id="calc-resource"></select>
        </label>
        <label>Amount / Day:
            <input type="number" id="calc-amount" value="100" min="1" step="1">
        </label>
        <label>Biome:
            <select id="calc-biome"></select>
        </label>
    </div>
    <div id="biome-description" class="biome-info"></div>
    <button class="calc-btn" id="calc-run">▶ Calculate Full Chain</button>
    <div class="calc-results" id="calc-output">
        <h4>Production Chain Visualization:</h4>
        <div id="calc-chain-tree"></div>
        <div style="border-top: 2px solid #562c1b; margin: 10px 0;"></div>
        <h4>Total Requirements:</h4>
        <div id="calc-list"></div>
    </div>
    <div class="calc-footer">Data: projectrebearth.com • Press C to toggle</div>
`;
document.body.appendChild(calcPanel);

// init selects
const calcResourceSelect = document.getElementById('calc-resource');
ALL_RESOURCES.forEach(res => { const opt = document.createElement('option'); opt.value = res; opt.textContent = res; calcResourceSelect.appendChild(opt); });
calcResourceSelect.addEventListener('change', () => { if(calcPanel.classList.contains('visible')) runCalculator(); });
const calcBiomeSelect = document.getElementById('calc-biome');
ALL_BIOMES.forEach(biome => { const opt = document.createElement('option'); opt.value = biome; opt.textContent = BIOMES[biome].name; calcBiomeSelect.appendChild(opt); });
calcBiomeSelect.addEventListener('change', () => {
    const biome = calcBiomeSelect.value;
    const info = BIOMES[biome];
    const descEl = document.getElementById('biome-description');
    descEl.textContent = info.description;
    descEl.style.background = info.color + '40';
    descEl.style.border = '1px solid ' + info.color;
    if(calcPanel.classList.contains('visible')) runCalculator();
});
calcBiomeSelect.dispatchEvent(new Event('change'));

// ui
const allUI = ['#hud_wrapper','#stats_wrapper','#menu','#minimap','#issues-button','#name_box'];
const nonCriticalUI = ['#stats_wrapper','#menu','#minimap','#issues-button','#name_box'];
 
function resetUI() { allUI.forEach(s => document.querySelector(s)?.classList.remove('ui-hidden-mod', 'ui-ghost-mod')); }
function updateBtnStates() {
    const hud = document.querySelector('#hud_wrapper');
    document.getElementById('btn-hide-ui')?.classList.toggle('active', hud?.classList.contains('ui-hidden-mod'));
    document.getElementById('btn-zen-ui')?.classList.toggle('active', !hud?.classList.contains('ui-hidden-mod') && document.querySelector('#menu')?.classList.contains('ui-hidden-mod'));
    document.getElementById('btn-ghost-ui')?.classList.toggle('active', hud?.classList.contains('ui-ghost-mod'));
}

document.getElementById('btn-hide-ui').onclick = () => { 
    const isH = document.querySelector('#hud_wrapper')?.classList.contains('ui-hidden-mod');
    resetUI(); if(!isH) allUI.forEach(s => document.querySelector(s)?.classList.add('ui-hidden-mod'));
    updateBtnStates();
};
document.getElementById('btn-zen-ui').onclick = () => {
    const isZ = document.querySelector('#menu')?.classList.contains('ui-hidden-mod');
    resetUI(); if(!isZ) nonCriticalUI.forEach(s => document.querySelector(s)?.classList.add('ui-hidden-mod'));
    updateBtnStates();
};
document.getElementById('btn-ghost-ui').onclick = () => {
    const isG = document.querySelector('#hud_wrapper')?.classList.contains('ui-ghost-mod');
    resetUI(); if(!isG) allUI.forEach(s => document.querySelector(s)?.classList.add('ui-ghost-mod'));
    updateBtnStates();
};
document.getElementById('btn-cinema').onclick = () => {
    document.body.classList.toggle('cinema-active');
    document.getElementById('btn-cinema').classList.toggle('active', document.body.classList.contains('cinema-active'));
};  

const applyFilter = (cls, btnId) => {
    const g = document.querySelector('#game') || document.body;
    const btn = document.getElementById(btnId);
    const active = g.classList.contains(cls);
    g.classList.remove('enhanced-visuals', 'golden-hour', 'deep-night');
    ['btn-enhance', 'btn-golden', 'btn-night'].forEach(id => document.getElementById(id)?.classList.remove('active'));
    if(!active) { g.classList.add(cls); btn?.classList.add('active'); }
};
document.getElementById('btn-enhance').onclick = () => applyFilter('enhanced-visuals', 'btn-enhance');
document.getElementById('btn-golden').onclick = () => applyFilter('golden-hour', 'btn-golden');
document.getElementById('btn-night').onclick = () => applyFilter('deep-night', 'btn-night');

// chain logic
const calcOutput = document.getElementById('calc-list');
const calcChainTree = document.getElementById('calc-chain-tree');

function toggleCalculator() {
    const isVisible = calcPanel.classList.contains('visible');
    calcPanel.classList.toggle('visible', !isVisible);
    if(!isVisible) runCalculator();
}
function closeCalculator() { calcPanel.classList.remove('visible'); }

function getConstructionCost(recipe, biome) {
    if(!recipe.construction) return {};
    if(recipe.construction[biome]) return recipe.construction[biome];
    if(recipe.constructionType === 'per_m2_wood') return {'Wood': recipe.construction[biome] || 0.01};
    return recipe.construction['Wood'] || recipe.construction['Stone'] || {};
}

function renderChainTree(chainData, level = 0) {
    let html = '';
    chainData.forEach(node => {
        const levelClass = level > 4 ? 'level-4' : 'level-' + level;
        const indent = '&nbsp;'.repeat(level * 4);
        html += `
            <div class="chain-node ${levelClass}">
                <div class="chain-header">
                    <span>${indent}◉ ${node.item} <span style="color:#c0392b">(${node.amount.toFixed(1)}/day)</span></span>
                </div>
                <div class="chain-details">
                    <span>◈ ${node.producer}</span>
                    ${node.buildings > 0 ? `<span>◇ ${Math.ceil(node.buildings)} buildings</span>` : ''}
                    ${node.population > 0 ? `<span>◇ ${node.population.toFixed(0)} workers</span>` : ''}
                </div>
            </div>
        `;
        if(node.inputs && node.inputs.length > 0) {
            html += `<div class="chain-arrow">${indent}⬇️ requires</div>`;
            html += renderChainTree(node.inputs, level + 1);
        }
    });
    return html;
}

function runCalculator() {
    const target = document.getElementById('calc-resource').value;
    const amount = parseFloat(document.getElementById('calc-amount').value) || 100;
    const biome = document.getElementById('calc-biome').value;
    const biomeData = BIOMES[biome];
    
    calcOutput.innerHTML = '';
    calcChainTree.innerHTML = '';
    
    const requirements = {};
    const buildingStats = {};
    const populationStats = {};
    const constructionCosts = {};
    const chainTree = [];
    
    // Build chain tree structure
    const rootNode = buildChainTree(target, amount, biome, biomeData, requirements, buildingStats, populationStats, constructionCosts);
    chainTree.push(rootNode);
    
    // Render Tree
    calcChainTree.innerHTML = renderChainTree(chainTree);
    
    // Render Totals
    const sorted = Object.entries(requirements).filter(([_, v]) => v > 0.01).sort((a, b) => b[1] - a[1]);
    if(sorted.length === 0) {
        calcOutput.innerHTML = '<div class="calc-row">No requirements found</div>';
        return;
    }
    
    sorted.forEach(([item, count]) => {
        const row = document.createElement('div');
        row.className = 'calc-row' + (item === target ? ' target' : '');
        const recipe = RECIPES[item];
        const producer = recipe ? recipe.produced_by : 'Raw / Natural';
        row.innerHTML = `<span>${item}</span> <span>${count.toFixed(1)}/day</span>`;
        calcOutput.appendChild(row);
        const prodRow = document.createElement('div');
        prodRow.className = 'calc-row producer';
        prodRow.textContent = `  →  ${producer}`;
        calcOutput.appendChild(prodRow);
    });
    
    // Buildings Summary
    const buildingEntries = Object.entries(buildingStats).filter(([_, v]) => v >= 1).sort((a, b) => b[1] - a[1]);
    if(buildingEntries.length > 0) {
        const sep = document.createElement('div'); sep.style.cssText = 'border-top: 2px solid #562c1b; margin: 10px 0;';
        calcOutput.appendChild(sep);
        const h = document.createElement('h4'); h.textContent = 'Total Buildings:'; h.style.cssText = 'margin: 10px 0 8px 0; font-size: 12px;';
        calcOutput.appendChild(h);
        buildingEntries.forEach(([building, count]) => {
            const r = document.createElement('div'); r.className = 'calc-row building';
            r.innerHTML = `<span>${building}</span> <span>${Math.ceil(count)} buildings</span>`;
            calcOutput.appendChild(r);
        });
    }
    
    // Population Summary
    const popEntries = Object.entries(populationStats).filter(([_, v]) => v > 0.001).sort((a, b) => b[1] - a[1]);
    if(popEntries.length > 0) {
        const totalPop = popEntries.reduce((s, [_, v]) => s + v, 0);
        const sep = document.createElement('div'); sep.style.cssText = 'border-top: 2px solid #562c1b; margin: 10px 0;';
        calcOutput.appendChild(sep);
        const h = document.createElement('h4'); h.textContent = 'Total Population:'; h.style.cssText = 'margin: 10px 0 8px 0; font-size: 12px;';
        calcOutput.appendChild(h);
        const summary = document.createElement('div'); summary.className = 'calc-summary';
        summary.innerHTML = `<div class="summary-row total"><span>Total Workers Needed:</span> <span>${Math.ceil(totalPop)} workers</span></div>`;
        calcOutput.appendChild(summary);
    }
    
    // Construction Summary
    const constructEntries = Object.entries(constructionCosts).filter(([_, v]) => v > 0.001).sort((a, b) => b[1] - a[1]);
    if(constructEntries.length > 0) {
        const sep = document.createElement('div'); sep.style.cssText = 'border-top: 2px solid #562c1b; margin: 10px 0;';
        calcOutput.appendChild(sep);
        const h = document.createElement('h4'); h.textContent = 'Construction Materials:'; h.style.cssText = 'margin: 10px 0 8px 0; font-size: 12px;';
        calcOutput.appendChild(h);
        constructEntries.forEach(([res, count]) => {
            const r = document.createElement('div'); r.className = 'calc-row construction';
            r.innerHTML = `<span>${res}</span> <span>${count.toFixed(1)}</span>`;
            calcOutput.appendChild(r);
        });
    }
}

function buildChainTree(item, neededAmount, biome, biomeData, requirements, buildingStats, populationStats, constructionCosts, depth = 0) {
    if(depth > 20) return null;
    
    requirements[item] = (requirements[item] || 0) + neededAmount;
    const recipe = RECIPES[item];
    
    const node = {
        item: item,
        amount: neededAmount,
        producer: recipe ? recipe.produced_by : 'Raw',
        buildings: 0,
        population: 0,
        inputs: []
    };
    
    // do not show too early...
    if(!recipe) {
        return node;
    }
    
    // biome aware out
    let outputPerBuilding = (typeof recipe.output === 'object')
        ? (recipe.output[biome] ?? recipe.output['Wood'] ?? 1)
        : (recipe.output || 1);

    if(outputPerBuilding <= 0) outputPerBuilding = 1;

    const buildingsNeeded = neededAmount / outputPerBuilding;
    const wholeBuildings = Math.ceil(buildingsNeeded);
    const buildingName = recipe.produced_by;
    
    if(buildingName && !buildingName.toLowerCase().includes('raw') && !buildingName.toLowerCase().includes('natural')) {
        node.buildings = buildingsNeeded;
        buildingStats[buildingName] = (buildingStats[buildingName] || 0) + buildingsNeeded;
        
        if(recipe.population) {
            const popNeeded = recipe.population * wholeBuildings;
            node.population = popNeeded;
            populationStats[buildingName] = (populationStats[buildingName] || 0) + popNeeded;
        }
        
        const biomeCosts = getConstructionCost(recipe, biome);
        for(const [res, qty] of Object.entries(biomeCosts)) {
            constructionCosts[res] = (constructionCosts[res] || 0) + (qty * wholeBuildings);
        }
    }
    
    // biome inputs
    if(recipe.inputs_biome && recipe.inputs_biome[biome]) {
        for(const [res, val] of Object.entries(recipe.inputs_biome[biome])) {
            const extra = val * buildingsNeeded;
            requirements[res] = (requirements[res] || 0) + extra;
        }
    }
    
    // exit
    if(!recipe.inputs || Object.keys(recipe.inputs).length === 0) {
        return node;
    }
    
    // recursion
    for(const [inputRes, inputAmt] of Object.entries(recipe.inputs)) {
        const inputTotal = inputAmt * buildingsNeeded;
        const childNode = buildChainTree(inputRes, inputTotal, biome, biomeData, requirements, buildingStats, populationStats, constructionCosts, depth + 1);
        if(childNode) node.inputs.push(childNode);
    }
    
    return node;
}

// event listeners
document.getElementById('calc-close').onclick = closeCalculator;
document.getElementById('calc-run').onclick = runCalculator;
document.getElementById('btn-calc').onclick = toggleCalculator;
calcPanel.addEventListener('click', (e) => { if(e.target === calcPanel) closeCalculator(); });
const togglePanel = () => panel.classList.toggle('collapsed');
document.getElementById('rebearth-mod-toggle').onclick = togglePanel;

// FPS counter
let times = [], fpsDisplay = document.getElementById('fps-display');
function refreshFPS() {
    window.requestAnimationFrame(() => {
        const now = performance.now();
        while(times.length > 0 && times[0] <= now - 1000) times.shift();
        times.push(now);
        if(fpsDisplay) fpsDisplay.innerText = "FPS: " + times.length;
        refreshFPS();
    });
}
refreshFPS();

// hotkeys
document.addEventListener('keydown', (e) => {
    if(e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;
    if(e.code === 'KeyC' && !e.ctrlKey && !e.metaKey) { e.preventDefault(); toggleCalculator(); return; }
    if(e.code === 'Escape' && calcPanel.classList.contains('visible')) { e.preventDefault(); closeCalculator(); return; }
    if(e.code === 'KeyH') document.getElementById('btn-hide-ui')?.click();
    if(e.code === 'KeyF') document.getElementById('btn-zen-ui')?.click();
    if(e.code === 'KeyT') document.getElementById('btn-ghost-ui')?.click();
    if(e.code === 'KeyV') document.getElementById('btn-enhance')?.click();
    if(e.code === 'KeyG') document.getElementById('btn-golden')?.click();
    if(e.code === 'KeyN') document.getElementById('btn-night')?.click();
    if(e.code === 'KeyL') document.getElementById('btn-cinema')?.click();
    if(e.code === 'KeyM') togglePanel();
});

// API
window.rebearthModTools = {
    getVersion: () => "1.2",
    getRecipes: () => RECIPES,
    getBiomes: () => BIOMES,
    calculate: (target, amount, biome) => {
        const reqs = {}, builds = {}, pops = {}, constructs = {};
        const biomeData = BIOMES[biome] || BIOMES['Wood'];
        buildChainTree(target, amount, biome, biomeData, reqs, builds, pops, constructs);
        return { requirements: reqs, buildings: builds, population: pops, construction: constructs };
    }
};
console.log("=RT= Rebearth Tools v1.2 loaded");
})();
"""


if __name__ == "__main__":
    ModManagerApp().mainloop()
