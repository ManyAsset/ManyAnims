import maya.cmds as cmds
import os
import sys
import maya.utils
import json

# Global variables
anim_path = None
export_path = None
normal_joints = []
ads_joints = []
default_namespace = ""  # sloth rig is iw4
selected_anim_files = []
export_cod4 = True
export_bo3 = False
# --- Add CAST LOGIC ---
export_cast = False
use_cast = True
use_se_mode = False
game_prefix = ""
export_selected_only = False
use_name_remap = False

# --- Save Settings ---
SETTINGS_FILE = os.path.join(os.getenv("APPDATA"),"ManyAnims","manyanims_settings.json")





#default settings
settings = {
    "use_cast": True,
    "use_se_mode": False,
    "export_cod4": True,
    "export_bo3": False,
    "default_namespace": "",
    "import_location": "",
    "export_location": "",
    "game_prefix": "",
    "use_name_remap": False
}


def ensure_setting_dir():
    """ENSURE THE MANYANIMS FOLDER EXISTS"""
    settings_dir = os.path.dirname(SETTINGS_FILE)
    if not os.path.exists(settings_dir):
        os.makedirs(settings_dir)


def load_settings():
    """Load settings from JSON file, or create defaults if missing."""
    global settings, use_cast, use_se_mode, export_cod4, export_bo3, default_namespace

    ensure_setting_dir()

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                saved = json.load(f)
                settings.update(saved)
                print("[ManyAnims] Loaded settings:", settings)
        except Exception as e:
            print("[ManyAnims] Failed to load settings:", e)
    else:
        save_settings()  # Save defaults on first run

    # Apply loaded values to globals
    use_cast = settings.get("use_cast", True)
    use_se_mode = settings.get("use_se_mode", False)
    export_cod4 = settings.get("export_cod4", True)
    export_bo3 = settings.get("export_bo3", False)
    default_namespace = settings.get("default_namespace", "")
    import_location = settings.get("import_location", "")
    export_location = settings.get("export_location", "")
    game_prefix = settings.get("game_prefix", "")
    global use_name_remap

    use_name_remap = settings.get("use_name_remap", False)

    # --- If the menu already exists, update checkboxes visually ---
    if cmds.menuItem("useCastMenuItem", exists=True):
        cmds.menuItem("useCastMenuItem", edit=True, checkBox=use_cast)
    if cmds.menuItem("useSEModeMenuItem", exists=True):
        cmds.menuItem("useSEModeMenuItem", edit=True, checkBox=use_se_mode)
    if cmds.menuItem("cod4ExportMenuItem", exists=True):
        cmds.menuItem("cod4ExportMenuItem", edit=True, checkBox=export_cod4)
    if cmds.menuItem("bo3ExportMenuItem", exists=True):
        cmds.menuItem("bo3ExportMenuItem", edit=True, checkBox=export_bo3)
    if cmds.menuItem("nameRemapMenuItem", exists=True):
        cmds.menuItem("nameRemapMenuItem", edit=True, checkBox=use_name_remap)


def save_settings():
    """Save current settings to JSON."""
    ensure_setting_dir()
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(settings, f, indent=4)
        print("[ManyAnims] Saved settings:", settings)
    except Exception as e:
        print("[ManyAnims] Failed to save settings:", e)


# Plugin loading functions
def add_setools_plugin_to_path():
    maya_plugin_paths = os.getenv('MAYA_PLUG_IN_PATH')
    
    if not maya_plugin_paths:
        print("Maya plugin path environment variable not set.")
        return False

    paths = maya_plugin_paths.split(';')

    for path in paths:
        plugin_path = os.path.join(path, 'SEToolsPlugin.py')
        if os.path.isfile(plugin_path):
            sys.path.append(path)
            print("SEToolsPlugin.py found. Added to sys.path: %s" % path)
            return True

    print("SEToolsPlugin.py not found in the Maya plugin paths.")
    return False

def add_maya_scripts_to_sys_path():
    maya_script_paths = os.getenv('MAYA_SCRIPT_PATH')

    if maya_script_paths:
        paths = maya_script_paths.split(os.pathsep)
        for path in paths:
            if path not in sys.path:
                print("Adding %s to sys.path" % path)
                sys.path.append(path)
        return True
    else:
        print("MAYA_SCRIPT_PATH environment variable not found.")
        return False

# Initialize plugins
plugin_found = add_setools_plugin_to_path()
if plugin_found:
    try:
        import SEToolsPlugin
        from SEToolsPlugin import __save_semodel__
    except:
        print("Failed to import SEToolsPlugin")

if add_maya_scripts_to_sys_path():
    try:
        import CoDMayaTools
        from CoDMayaTools import OBJECT_NAMES, CreateXModelWindow, GeneralWindow_ExportSelected
        print("Successfully imported CoDMayaTools")
    except ImportError as e:
        print("Error importing CoDMayaTools: %s" % str(e))
else:
    print("Could not add Maya scripts to sys.path")



def select_anim_files_dialog(*args):
    global anim_path, selected_anim_files

    file_filter = "*.cast" if use_cast else "*.seanim"
    caption = "Select CAST Files to Export" if use_cast else "Select SEAnim Files to Export"

    # Start from saved import location if exists, otherwise project root
    start_dir = settings.get("import_location", "")
    if not start_dir or not os.path.exists(start_dir):
        start_dir = cmds.workspace(q=True, rd=True)

    selected = cmds.fileDialog2(fileMode=4, dialogStyle=2, caption=caption,
                                fileFilter=file_filter, startingDirectory=start_dir)

    if selected:
        selected_anim_files = selected
        anim_path = os.path.dirname(selected[0])

        print(f"[ManyAnims] Animation path set to: {anim_path}")
        print(f"[ManyAnims] Selected {len(selected_anim_files)} file(s)")
        cmds.confirmDialog(
            title="Animations Selected",
            message=f"Selected {len(selected_anim_files)} animation(s).",
            button=["OK"]
        )
        enable_ui_elements_if_paths_selected()
    else:
        selected_anim_files = []
        cmds.confirmDialog(title="No Selection", message="No animations selected.", button=["OK"])




def set_import_location(*args):
    selected = cmds.fileDialog2(fileMode=3, dialogStyle=2, caption="Select Default Import Folder")
    if selected:
        settings["import_location"] = selected[0]
        save_settings()
        cmds.confirmDialog(title="Import Location Set",
                           message=f"Default import folder set to:\n{selected[0]}", button=["OK"])

def set_export_location(*args):
    selected = cmds.fileDialog2(fileMode=3, dialogStyle=2, caption="Select Default Export Folder")
    if selected:
        settings["export_location"] = selected[0]
        save_settings()
        cmds.confirmDialog(title="Export Location Set",
                           message=f"Default export folder set to:\n{selected[0]}", button=["OK"])


def select_normal_joints(*args):
    selected_joints = cmds.ls(selection=True)
    if selected_joints:
        global normal_joints
        normal_joints = selected_joints
        trigger_export_if_all_selected()
    else:
        cmds.confirmDialog(title="Error", message="Please select joints for Normal animation.", button=["OK"])

def select_ads_joints(*args):
    selected_joints = cmds.ls(selection=True)
    if selected_joints:
        global ads_joints
        ads_joints = selected_joints
        trigger_export_if_all_selected()
    else:
        cmds.confirmDialog(title="Error", message="Please select joints for ADS animation.", button=["OK"])

def on_treyarch_checked(*args):
    if cmds.menuItem(treyarch_checkbox, query=True, checkBox=True):
        cmds.menuItem(iw_sh_checkbox, edit=True, checkBox=False)
        if anim_path and export_path:
            if use_cast:
                load_cast_from_path(anim_path)
            else:
                load_seanim_from_path(anim_path)
        else:
            cmds.confirmDialog(title="Error", message="Please select both Anim Path and Export Path first.", button=["OK"])

def on_iw_sh_checked(*args):
    if cmds.menuItem(iw_sh_checkbox, query=True, checkBox=True):
        cmds.menuItem(treyarch_checkbox, edit=True, checkBox=False)
        if anim_path and export_path:
            if use_cast:
                load_cast_from_path(anim_path)
            else:
                load_seanim_from_path(anim_path)
        else:
            cmds.confirmDialog(title="Error", message="Please select both Anim Path and Export Path first.", button=["OK"])

def toggle_cod4_export(*args):
    global export_cod4, export_bo3
    export_cod4 = True
    export_bo3 = False
    cmds.menuItem("cod4ExportMenuItem", edit=True, checkBox=export_cod4)
    cmds.menuItem("bo3ExportMenuItem", edit=True, checkBox=export_bo3)
    print("[ManyAnims] Export for CoD4: %s" % export_cod4)

    # Save setting
    settings["export_cod4"] = export_cod4
    settings["export_bo3"] = export_bo3
    save_settings()




    # Rest of existing logic...
    CoDMayaTools.SetCurrentGame("CoD4")
    auto_rename_state = CoDMayaTools.QueryToggableOption("AutomaticRename")
    if auto_rename_state:
        CoDMayaTools.SetToggableOption("AutomaticRename")
    cmds.evalDeferred("CoDMayaTools.CreateMenu()")


def toggle_export_selected_only(*args):
    global export_selected_only

    export_selected_only = not export_selected_only
    cmds.menuItem("exportSelectedMenuItem", edit=True, checkBox=export_selected_only)

    print(f"[ManyAnims] Export Selected Only Mode: {export_selected_only}")

    # -------------------------------------------------
    # AUTO TRIGGER EXPORT WHEN ENABLED
    # -------------------------------------------------
    if export_selected_only:

        if not anim_path or not export_path:
            cmds.confirmDialog(
                title="Error",
                message="Please select both Anim Path and Export Path first.",
                button=["OK"]
            )
            return

        current_selection = cmds.ls(selection=True)

        if not current_selection:
            cmds.confirmDialog(
                title="Error",
                message="No joints selected!",
                button=["OK"]
            )
            return

        print("[ManyAnims] Auto-triggering export using selected joints...")

        # Trigger export loop
        if use_cast:
            load_cast_from_path(anim_path)
        else:
            load_seanim_from_path(anim_path)


def toggle_bo3_export(*args):
    global export_bo3, export_cod4
    export_bo3 = True
    export_cod4 = False
    cmds.menuItem("bo3ExportMenuItem", edit=True, checkBox=export_bo3)
    cmds.menuItem("cod4ExportMenuItem", edit=True, checkBox=export_cod4)
    print("[ManyAnims] Export for BO3: %s" % export_bo3)

    # Save setting
    settings["export_bo3"] = export_bo3
    settings["export_cod4"] = export_cod4
    save_settings()

    # Rest of existing logic...
    CoDMayaTools.SetCurrentGame("CoD12")
    auto_rename_state = CoDMayaTools.QueryToggableOption("AutomaticRename")
    if not auto_rename_state:
        CoDMayaTools.SetToggableOption("AutomaticRename")
    cmds.evalDeferred("CoDMayaTools.CreateMenu()")

def force_update_codmaya_menu_checkbox(item_name, desired_state):
    if cmds.menuItem(item_name, exists=True):
        cmds.menuItem(item_name, edit=True, checkBox=desired_state)

def create_progress_bar(numfiles):
    # Remove existing window if open
    if cmds.window("ManyAsserts_progress", exists=True):
        cmds.deleteUI("ManyAsserts_progress")

    # Create compact, borderless window
    window = cmds.window(
        "ManyAsserts_progress",
        title="Exporting Animations",
        sizeable=False,
        minimizeButton=False,
        maximizeButton=False,
        widthHeight=(320, 45)
    )

    # Use a formLayout to eliminate any internal padding
    form = cmds.formLayout()
    progress = cmds.progressBar("ManyAsserts_progress", maxValue=numfiles, height=20, width=300)

    # Attach progress bar to all sides (flush fit)
    cmds.formLayout(form, edit=True,
        attachForm=[(progress, 'top', 5), (progress, 'left', 10), (progress, 'right', 10), (progress, 'bottom', 5)]
    )

    cmds.showWindow(window)
    return progress


def update_progress_bar(progress_control, current_value):
    cmds.progressBar(progress_control, edit=True, progress=current_value)
    cmds.refresh()

def close_progress_bar():
    if cmds.control("ManyAsserts_progress", exists=True):
        cmds.deleteUI("ManyAsserts_progress")

def set_anim_path(*args):
    global anim_path
    selected = cmds.fileDialog2(fileMode=3, dialogStyle=2, caption="Select Animation Folder")
    if selected:
        anim_path = selected[0]
        cmds.confirmDialog(title="Anim Path Selected", message="Anim Path: " + anim_path, button=["OK"])
        enable_ui_elements_if_paths_selected()

def set_export_path(*args):
    global export_path
    start_dir = settings.get("export_location", "")
    if not start_dir or not os.path.exists(start_dir):
        start_dir = cmds.workspace(q=True, rd=True)

    selected = cmds.fileDialog2(fileMode=3, dialogStyle=2, caption="Select Export Folder",
                                startingDirectory=start_dir)

    if selected:
        export_path = selected[0]
        cmds.confirmDialog(title="Export Path Selected",
                           message=f"Export Path: {export_path}", button=["OK"])
        enable_ui_elements_if_paths_selected()


def enable_ui_elements_if_paths_selected():
    global anim_path, export_path
    if anim_path and export_path:
        toggle_ui_elements(True)

def toggle_ui_elements(enable):
    cmds.menuItem(treyarch_checkbox, edit=True, enable=enable)
    cmds.menuItem(iw_sh_checkbox, edit=True, enable=enable)
    cmds.menuItem(export_selected_menu_item, edit=True, enable=enable)
    #cmds.menuItem(select_normal_joints_button, edit=True, enable=enable)
    #cmds.menuItem(select_ads_joints_button, edit=True, enable=enable)

def trigger_export_if_all_selected():
    global export_selected_only

    # --- NEW MODE: Live Selection Only ---
    if export_selected_only:
        if anim_path and export_path:
            if use_cast:
                load_cast_from_path(anim_path)
            else:
                load_seanim_from_path(anim_path)
        else:
            cmds.confirmDialog(title="Error",
                               message="Please select both Anim Path and Export Path first.",
                               button=["OK"])
        return

    # --- ORIGINAL BEHAVIOR ---
    if normal_joints and ads_joints:
        if anim_path and export_path:
            if use_cast:
                load_cast_from_path(anim_path)
            else:
                load_seanim_from_path(anim_path)
        else:
            cmds.confirmDialog(title="Error",
                               message="Please select both Anim Path and Export Path first.",
                               button=["OK"])


def remap_anim_names(name):
    """Rename anim filenames."""
    name = name.replace("fast", "quick")
    name = name.replace("reload_intro", "reload_in")
    name = name.replace("first_pullout", "raise_first")
    name = name.replace("first_time_pullout", "raise_first")
    name = name.replace("first_raise", "raise_first")
    name = name.replace("pullout_first ", "raise_first")
    name = name.replace("lastshot", "fire_last")
    name = name.replace("last_shot", "fire_last")
    name = name.replace("lastfire", "fire_last")
    name = name.replace("ads_rechamber", "rechamber_ads")
    name = name.replace("ads_base_up", "ads_up")
    name = name.replace("ads_base_down", "ads_down")
    name = name.replace("viewmodel", "vm")
    name = name.replace("va_", "vm_")
    name = name.replace("ads_fire", "fire_ads")
    name = name.replace("putaway", "drop")
    name = name.replace("pullout", "raise")
    return name


def load_seanim_from_path(anim_path):
    # Collect only .seanim files, even if selected_anim_files has mixed entries
    files_to_process = [
        f for f in (selected_anim_files or [
            os.path.join(anim_path, f) for f in os.listdir(anim_path)
        ])
        if f.lower().endswith(".seanim")
    ]

    if not files_to_process:
        cmds.confirmDialog(title="No Animations", message="No .seanim files to process.", button=["OK"])
        return

    progress_control = create_progress_bar(len(files_to_process))

    for idx, anim_file_path in enumerate(files_to_process, 1):
        anim_file = os.path.basename(anim_file_path)

        # 🔒 Extra safety: skip if extension isn’t .seanim
        if not anim_file_path.lower().endswith(".seanim"):
            print(f"[ManyAnims] ⚠️ Skipping non-SEAnim file: {anim_file_path}")
            continue

        print("Loading animation file: %s" % anim_file_path)
        SEToolsPlugin.__load_seanim__(anim_file_path, scene_time=False, blend_anim=False)

        if export_selected_only:
            method = "manual"
        elif cmds.menuItem(treyarch_checkbox, query=True, checkBox=True):
            method = "treyarch"
        else:
            method = "iw/sh"

        export_xanim_file(
            anim_file_path,
            export_path,
            method_type=method
        )


        update_progress_bar(progress_control, idx)

    close_progress_bar()
    print("Processed %d SEAnim animation(s)." % len(files_to_process))

    # Reset scene after all SEAnims are processed
    if hasattr(SEToolsPlugin, '__scene_resetanim__'):
        print("[ManyAnims] Resetting scene after export...")
        SEToolsPlugin.__scene_resetanim__()
    else:
        print("[ManyAnims] Warning: __scene_resetanim__ not found in SEToolsPlugin")

    # --- Reset export mode checkboxes ---
    cmds.menuItem(treyarch_checkbox, edit=True, checkBox=False)
    cmds.menuItem(iw_sh_checkbox, edit=True, checkBox=False)
    print("[ManyAnims] Reset Treyarch/IW-SH checkboxes after export.")
    reset_export_selected_mode()


original_save_reminder = CoDMayaTools.SaveReminder

def modified_save_reminder(allow_unsaved=True):
    return True

def export_xanim_file(input_file_path, output_directory, method_type="treyarch"):
    ext = ".xanim_export" if export_cod4 else ".xanim_bin" if export_bo3 else ".xanim_export"
    # --- CLEAN FILENAME (remap anim names) ---
    base = os.path.basename(input_file_path).replace(".seanim", "")
    if use_name_remap:
        base = remap_anim_names(base) # Rename anim filename
    base = apply_game_prefix(base)

    # Re-append extension
    output_file_path = os.path.join(output_directory, base + ext)

    print(f"[ManyAnims] Remapped output filename → {output_file_path}")
    print("Exporting to path: %s" % output_file_path)

    filename_lower = os.path.basename(input_file_path).lower() # added on 18/02/26 - added support for ads anims that have base in the name is before was skipped.
    is_ads = (
        "ads_up" in filename_lower
        or "ads_down" in filename_lower
        or "ads_base_up" in filename_lower
        or "ads_base_down" in filename_lower
    )

    # --- Joint selection logic ---
    if method_type == "manual":

        current_selection = cmds.ls(selection=True)

        # -----------------------------
        # Export Selected Only Mode
        # -----------------------------
        if export_selected_only:

            if not current_selection:
                cmds.confirmDialog(
                    title="Error",
                    message="Export Selected Only mode is enabled but no joints are selected!",
                    button=["OK"]
                )
                return

            print(f"[ManyAnims] Export Selected Only → Using current selection: {current_selection}")
            cmds.select(clear=True)
            for j in current_selection:
                cmds.select(j, add=True, hierarchy=True)

        # -----------------------------
        # Standard Manual Mode
        # -----------------------------
        else:

            if current_selection:
                print(f"[ManyAnims] Manual Mode → Using current selection: {current_selection}")
                cmds.select(current_selection)

            else:
                print("[ManyAnims] Manual Mode → No current selection. Falling back to stored joints.")

                if is_ads and ads_joints:
                    print(f"[ManyAnims] Using stored ADS joints: {ads_joints}")
                    cmds.select(ads_joints)

                elif normal_joints:
                    print(f"[ManyAnims] Using stored Normal joints: {normal_joints}")
                    cmds.select(normal_joints)

                else:
                    cmds.confirmDialog(
                        title="Error",
                        message="No joints selected and no stored joints available!",
                        button=["OK"]
                    )
                    return

    elif method_type == "treyarch":

        if is_ads:
            cmds.select(f"{default_namespace}:tag_view",
                        f"{default_namespace}:tag_torso")
        else:
            cmds.select(f"{default_namespace}:tag_torso",
                        f"{default_namespace}:tag_cambone",
                        hierarchy=True)

    elif method_type == "iw/sh":

        if is_ads:
            if cmds.objExists(f"{default_namespace}:tag_ads"):
                cmds.select(f"{default_namespace}:tag_view",
                            f"{default_namespace}:tag_ads")
            else:
                cmds.confirmDialog(
                    title="Error",
                    message=f"ADS joints ('{default_namespace}:tag_ads') not found!",
                    button=["OK"]
                )
                return
        else:
            if cmds.objExists(f"{default_namespace}:tag_ads") and cmds.objExists(f"{default_namespace}:tag_cambone"):
                cmds.select(f"{default_namespace}:tag_ads",
                            f"{default_namespace}:tag_cambone",
                            hierarchy=True)
            else:
                cmds.confirmDialog(
                    title="Error",
                    message=f"Required joints not found in namespace '{default_namespace}'!",
                    button=["OK"]
                )
                return


    # --- Setup CoDMayaTools for export ---
    CoDMayaTools.SaveReminder = modified_save_reminder
    CoDMayaTools.RefreshXAnimWindow()
    
    textFieldName = CoDMayaTools.OBJECT_NAMES['xanim'][0] + "_SaveToField"
    cmds.textField(textFieldName, edit=True, text=output_file_path)
    CoDMayaTools.SetFrames('xanim')
    
    fpsFieldName = CoDMayaTools.OBJECT_NAMES['xanim'][0] + "_FPSField"
    cmds.intField(fpsFieldName, edit=True, value=30)
    qualityField = CoDMayaTools.OBJECT_NAMES['xanim'][0] + "_qualityField"
    cmds.intField(qualityField, edit=True, value=0)
    CoDMayaTools.ReadNotetracks('xanim')

    # --- Clean notetracks (RemoveAudioOneShot calls RefreshXAnimWindow internally,
    #     which wipes the SaveToField — so we re-apply all export fields afterwards) ---
    try:
        CoDMayaTools.RemoveUnusableNotes('xanim')
        print("[ManyAnims] Removed unusable notetracks.")
    except Exception as e:
        print(f"[ManyAnims] Failed to remove unusable notetracks: {e}")
    try:
        CoDMayaTools.RemoveAudioOneShot('xanim')
        print("[ManyAnims] Stripped AudioOneShot prefixes from notetracks.")
    except Exception as e:
        print(f"[ManyAnims] Failed to strip AudioOneShot notetracks: {e}")

    # Re-apply export fields that RefreshXAnimWindow may have wiped
    cmds.textField(textFieldName, edit=True, text=output_file_path)
    cmds.intField(fpsFieldName, edit=True, value=30)
    cmds.intField(qualityField, edit=True, value=0)

    # --- Suppress CoDMayaTools progress window ---
    _original_window = cmds.window  # save original reference
    _original_show_window = cmds.showWindow  # also intercept showWindow (safety)

    def _silent_window(*args, **kwargs):
        """Safely suppress CoDMayaTools progress window without recursion or visibility."""
        name_arg = args[0] if args and isinstance(args[0], str) else ""
        title = kwargs.get("title", "")

        if (name_arg and name_arg.startswith("wprogress")) or ("Export" in title or "Progress" in title):
            hidden_name = "wprogress_hidden_safe"
            if not _original_window(hidden_name, exists=True):  # use original function only
                _original_window(hidden_name,
                                 title="Hidden Progress",
                                 visible=False,
                                 topEdge=-10000,
                                 leftEdge=-10000,
                                 widthHeight=(1, 1))
            print(f"[ManyAnims] 🧩 Suppressing CoDMayaTools progress window: {name_arg or title}")
            return hidden_name

        return _original_window(*args, **kwargs)

    try:
        cmds.window = _silent_window
        cmds.showWindow = lambda *args, **kwargs: None  # block forced popup
        CoDMayaTools.GeneralWindow_ExportSelected('xanim', exportingMultiple=False)
    finally:
        cmds.window = _original_window
        cmds.showWindow = _original_show_window
        CoDMayaTools.ClearNotes('xanim')
        CoDMayaTools.SaveReminder = original_save_reminder



def show_about_dialog(*args):
    if cmds.window("manyanimsAboutWindow", exists=True):
        cmds.deleteUI("manyanimsAboutWindow")

    try:
        if cmds.windowPref("manyanimsAboutWindow", exists=True):
            cmds.windowPref("manyanimsAboutWindow", remove=True)
    except:
        pass

    window = cmds.window(
        "manyanimsAboutWindow",
        title="About ManyAnims",
        sizeable=False,
        minimizeButton=False,
        maximizeButton=False
    )

    # Outer column with padding
    cmds.columnLayout(adjustableColumn=True, rowSpacing=0, columnOffset=("both", 20))

    cmds.separator(style="none", height=16)

    # Tool name (bold + large feel via boldLabelFont)
    cmds.text(label="ManyAnims Tool for Maya", font="boldLabelFont", align="center", height=22)
    cmds.separator(style="none", height=4)
    cmds.text(label="Batch Animation Exporter", font="smallPlainLabelFont", align="center", height=16)
    cmds.text(label="Created by elfenliedtopfan5 for Sloth", font="smallPlainLabelFont", align="center", height=16)

    cmds.separator(style="none", height=12)
    cmds.separator(style="in", height=1)
    cmds.separator(style="none", height=12)

    # Changelog header
    cmds.text(label="Changelog", font="boldLabelFont", align="left", height=18)
    cmds.separator(style="none", height=8)

    # Changelog entries — each as a two-part row: version tag + description
    changelog = [
        ("1.3.0", "Fixed BO3, BO4 and CW not exporting correct ads tags. Added anim auto rename and prefix option."),
        ("1.2.1", "Fixed set import and export location bug."),
        ("1.2.0", "Added set import/export location, fixed progress bar, added COD1 and COD2 rig converter support."),
        ("1.1.0", "Cast support and UI changes."),
        ("1.0.0", "Initial release."),
    ]

    for version, desc in changelog:
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(60, 460), columnAlign2=("left", "left"), columnOffset2=(0, 8))
        cmds.text(label="v{}".format(version), font="boldLabelFont", align="left")
        cmds.text(label=desc, font="smallPlainLabelFont", align="left", wordWrap=True)
        cmds.setParent("..")  # rowLayout
        cmds.separator(style="none", height=5)

    cmds.separator(style="none", height=12)
    cmds.separator(style="in", height=1)
    cmds.separator(style="none", height=10)

    # OK button centered
    cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnWidth3=(180, 100, 180))
    cmds.separator(style="none")
    cmds.button(
        label="OK",
        height=28,
        command=lambda x: cmds.deleteUI("manyanimsAboutWindow")
    )
    cmds.separator(style="none")
    cmds.setParent("..")  # rowLayout

    cmds.separator(style="none", height=12)

    cmds.showWindow(window)
    cmds.window(window, edit=True, widthHeight=(560, 340))

def open_namespace_dialog(*args):
    global default_namespace
    result = cmds.promptDialog(
        title="Set Namespace",
        message="Enter Default Namespace:",
        button=["OK", "Cancel"],
        defaultButton="OK",
        cancelButton="Cancel",
        dismissString="Cancel",
        text=default_namespace
    )
    if result == "OK":
        default_namespace = cmds.promptDialog(query=True, text=True)
        print("[ManyAnims] Namespace set to: %s" % default_namespace)




# CAST SUPPORT ADD HERE ELFENLIEDTOPFAN5 19/09/2025 TAKEN FROM DERIVED FROM ALICE LOAD METHORD ON 01/09/25

def reset():
    try:
        import castplugin
        castplugin.utilityClearAnimation()
        print("[ManyAnims] Manual Reset Triggered")
    except Exception as e:
        print(f"[ManyAnims] Reset failed: {e}")

# --- Toggle CAST export ---
def toggle_use_cast(*args):
    global use_cast, use_se_mode
    use_cast = not use_cast
    use_se_mode = not use_cast  # Opposite
    cmds.menuItem("useCastMenuItem", edit=True, checkBox=use_cast)
    cmds.menuItem("useSEModeMenuItem", edit=True, checkBox=use_se_mode)
    print(f"[ManyAnims] CAST Mode: {use_cast}, SE Mode: {use_se_mode}")

    # Save to settings
    settings["use_cast"] = use_cast
    settings["use_se_mode"] = use_se_mode
    save_settings()

def toggle_se_mode(*args):
    global use_se_mode, use_cast
    use_se_mode = not use_se_mode
    use_cast = not use_se_mode  # Opposite
    cmds.menuItem("useSEModeMenuItem", edit=True, checkBox=use_se_mode)
    cmds.menuItem("useCastMenuItem", edit=True, checkBox=use_cast)
    print(f"[ManyAnims] SE Mode: {use_se_mode}, CAST Mode: {use_cast}")

    # Save to settings
    settings["use_se_mode"] = use_se_mode
    settings["use_cast"] = use_cast
    save_settings()


def toggle_name_remap(*args):
    global use_name_remap

    use_name_remap = not use_name_remap
    cmds.menuItem("nameRemapMenuItem", edit=True, checkBox=use_name_remap)

    settings["use_name_remap"] = use_name_remap
    save_settings()

    print(f"[ManyAnims] Filename Remapping Enabled: {use_name_remap}")



def set_game_prefix(*args):
    global game_prefix
    result = cmds.promptDialog(
        title="Set Game Prefix",
        message="Enter Game Prefix (e.g t6, iw3):",
        button=["OK", "Clear", "Cancel"],
        defaultButton="OK",
        cancelButton="Cancel",
        dismissString="Cancel",
        text=game_prefix
    )

    if result == "OK":
        game_prefix = cmds.promptDialog(query=True, text=True).strip().lower()
        settings["game_prefix"] = game_prefix
        save_settings()
        cmds.confirmDialog(title="Game Prefix Set", message=f"Game Prefix set to:\n{game_prefix}")
    elif result == "Clear":
        game_prefix = ""
        settings["game_prefix"] = ""
        save_settings()
        cmds.confirmDialog(title="Game Prefix Cleared", message="Game Prefix removed.")


def apply_game_prefix(name):
    """Insert game prefix after the first vm_ or va_ anywhere in the name."""
    if not game_prefix:
        return name

    # Replace the FIRST vm_ only
    if "vm_" in name:
        return name.replace("vm_", f"vm_{game_prefix}_", 1)

    # Replace the FIRST va_ only
    if "va_" in name:
        return name.replace("va_", f"va_{game_prefix}_", 1)

    return name



def hide_codmaya_progress_window():
    """Hide CoDMayaTools internal progress window if it appears."""
    try:
        for w in cmds.lsUI(type="window"):
            if "Progress" in w and ("CoDMayaTools" in w or "GeneralWindow" in w):
                cmds.deleteUI(w)
                print("[ManyAnims]  Suppressed CoDMayaTools internal progress bar:", w)
    except Exception as e:
        print(f"[ManyAnims]  Could not hide CoDMayaTools progress bar: {e}")
    


# --- Load CAST files ---
def load_cast_from_path(anim_path):
    try:
        import castplugin
    except ImportError:
        cmds.warning(" castplugin not found. Cannot import CAST files.")
        return

    # Collect all .cast files (or use selected)
    files_to_process = selected_anim_files or [
        os.path.join(anim_path, f) for f in os.listdir(anim_path) if f.lower().endswith(".cast")
    ]
    if not files_to_process:
        cmds.confirmDialog(title="No Animations", message="No .cast files to process.", button=["OK"])
        return

    progress_control = create_progress_bar(len(files_to_process))

    # --- Cache original manual selection BEFORE CAST modifies it
    cached_manual_selection = cmds.ls(selection=True)

    for idx, cast_file_path in enumerate(files_to_process, 1):
        cast_file = os.path.basename(cast_file_path)
        print(f"[ManyAnims] Loading CAST animation: {cast_file_path}")

        # --- Clear animation keys
        joints = cmds.ls(type="joint")
        if joints:
            cmds.cutKey(joints, time=(), option="keys")


        # --- Check for specific rig joint groups before clearing notetracks ---
        rig_joint_groups = {"tx:Joints", "iw2:Joints", "iw3:Joints"}
        scene_transforms = set(cmds.ls(type='transform'))

        # Look for any of the exact groups in the scene
        found_rig_groups = rig_joint_groups.intersection(scene_transforms)

        if found_rig_groups:
            print(f"[ManyAnims]  Found special rig joint group(s): {list(found_rig_groups)} → Skipping ClearAndRemoveCastNotetracks()")
        else:
            try:
                CoDMayaTools.ClearAndRemoveCastNotetracks("xanim")
                print("[ManyAnims]  Cleared and removed CAST notetracks.")
            except Exception as e:
                print(f"[ManyAnims]  Failed to clear CAST notetracks: {e}")
                
        castplugin.importCast(cast_file_path)

        # --- Determine export extension (.xanim_bin / .xanim_export)
        ext = ".xanim_export" if export_cod4 else ".xanim_bin"
        # --- CLEAN FILENAME (remap anim names) ---
        base = cast_file.replace(".cast", "")
        if use_name_remap:
            base = remap_anim_names(base)
        base = apply_game_prefix(base)

        output_file_path = os.path.join(export_path, base + ext)

        print(f"[ManyAnims] Remapped CAST output filename → {output_file_path}")

        print(f"[ManyAnims] Exporting to: {output_file_path}")

        # --- Refresh CoDMayaTools and prepare export
        CoDMayaTools.RefreshXAnimWindow()
        CoDMayaTools.SaveReminder = modified_save_reminder

        # Set export fields
        textFieldName = CoDMayaTools.OBJECT_NAMES['xanim'][0] + "_SaveToField"
        cmds.textField(textFieldName, edit=True, text=output_file_path)
        print(f"Exporting To: {textFieldName}")
        CoDMayaTools.SetFrames('xanim')
        fpsFieldName = CoDMayaTools.OBJECT_NAMES['xanim'][0] + "_FPSField"
        cmds.intField(fpsFieldName, edit=True, value=30)
        qualityField = CoDMayaTools.OBJECT_NAMES['xanim'][0] + "_qualityField"
        cmds.intField(qualityField, edit=True, value=0)

        # --- Determine method type
        #method_type = "treyarch" if cmds.menuItem(treyarch_checkbox, query=True, checkBox=True) else "iw/sh" 
        if export_selected_only:
            method_type = "manual"
        elif cmds.menuItem(treyarch_checkbox, query=True, checkBox=True):
            method_type = "treyarch"
        else:
            method_type = "iw/sh"
        fname = cast_file.lower() # have added in support for base as well 18/02/26
        is_ads = (
            "ads_up" in fname
            or "ads_down" in fname
            or "ads_base_up" in fname
            or "ads_base_down" in fname
        )

        # --- Joint selection
        try:
            if method_type == "manual":

                current_selection = cached_manual_selection

                if not current_selection:
                    cmds.confirmDialog(
                        title="Error",
                        message="No joints selected for manual export!",
                        button=["OK"]
                    )
                    continue

                print(f"[ManyAnims] CAST Manual Mode → Using current selection: {current_selection}")
                cmds.select(clear=True)
                for j in current_selection:
                    if cmds.objExists(j):
                        cmds.select(j, add=True)

            elif method_type == "treyarch":

                if is_ads:
                    cmds.select(f"{default_namespace}:tag_view",
                                f"{default_namespace}:tag_torso")
                else:
                    cmds.select(f"{default_namespace}:tag_torso",
                                f"{default_namespace}:tag_cambone",
                                hierarchy=True)

            elif method_type == "iw/sh":

                if is_ads:
                    if cmds.objExists(f"{default_namespace}:tag_ads"):
                        cmds.select(f"{default_namespace}:tag_view",
                                    f"{default_namespace}:tag_ads")
                    else:
                        cmds.confirmDialog(
                            title="Error",
                            message=f"ADS joint ('{default_namespace}:tag_ads') not found!",
                            button=["OK"]
                        )
                        continue
                else:
                    if cmds.objExists(f"{default_namespace}:tag_ads") and cmds.objExists(f"{default_namespace}:tag_cambone"):
                        cmds.select(f"{default_namespace}:tag_ads",
                                    f"{default_namespace}:tag_cambone",
                                    hierarchy=True)
                    else:
                        cmds.confirmDialog(
                            title="Error",
                            message=f"Required joints not found in namespace '{default_namespace}'!",
                            button=["OK"]
                        )
                        continue

        except Exception as e:
            cmds.warning(f"[ManyAnims]  Failed to select joints for {cast_file}: {e}")
            continue

        # --- Read notetracks (only if CastNotetracks node exists in scene)
        has_cast_notetracks = cmds.objExists("CastNotetracks")
        if has_cast_notetracks:
            try:
                CoDMayaTools.ReadNotetracks('xanim')
                print("[ManyAnims] Read CAST notetracks.")
            except Exception as e:
                print(f"[ManyAnims]  Failed to read notetracks: {e}")

            # --- Clean notetracks (RemoveAudioOneShot calls RefreshXAnimWindow internally,
            #     which wipes the SaveToField — so we re-apply the path afterwards) ---
            try:
                CoDMayaTools.RemoveUnusableNotes('xanim')
                print("[ManyAnims] Removed unusable notetracks.")
            except Exception as e:
                print(f"[ManyAnims]  Failed to remove unusable notetracks: {e}")
            try:
                CoDMayaTools.RemoveAudioOneShot('xanim')
                print("[ManyAnims] Stripped AudioOneShot prefixes from notetracks.")
            except Exception as e:
                print(f"[ManyAnims]  Failed to strip AudioOneShot notetracks: {e}")

            # Re-apply export fields that RefreshXAnimWindow may have wiped
            cmds.textField(textFieldName, edit=True, text=output_file_path)
            cmds.intField(fpsFieldName, edit=True, value=30)
            cmds.intField(qualityField, edit=True, value=0)
        else:
            print("[ManyAnims] No CastNotetracks node found — skipping notetrack read/clean.")



        # --- Suppress CoDMayaTools progress bar
        _original_window = cmds.window

        def _silent_window(*args, **kwargs):
            name_arg = args[0] if args and isinstance(args[0], str) else ""
            title = kwargs.get("title", "")
            if (name_arg and name_arg.startswith("wprogress")) or ("Export" in title or "Progress" in title):
                hidden_name = "wprogress_hidden_safe"
                if not _original_window(hidden_name, exists=True):
                    _original_window(hidden_name, title="Hidden Progress", visible=False,
                                     topEdge=-10000, leftEdge=-10000, widthHeight=(1, 1))
                print(f"[ManyAnims] 🧩 Suppressing CoDMayaTools progress window: {name_arg or title}")
                return hidden_name
            return _original_window(*args, **kwargs)

        cmds.window = _silent_window


        # --- Export animation and safely clear notetracks
        try:
            CoDMayaTools.GeneralWindow_ExportSelected('xanim', False)
            castplugin.utilityClearAnimation()

            # -----------------------------
            # Manual Mode Reset Per Anim
            # -----------------------------
            if method_type == "manual":
                try:
                    castplugin.utilityClearAnimation()
                    print("[ManyAnims] Manual mode → resetting scene per anim (CAST)")
                except Exception as e:
                    print(f"[ManyAnims] Manual reset failed: {e}")

            # --- check for Joint Groups before clearing notetracks ---

            # --- Check for specific rig joint groups before clearing notetracks ---
            rig_joint_groups = {"tx:Joints", "iw2:Joints", "iw3:Joints"}
            scene_transforms = set(cmds.ls(type='transform'))

            # Look for any of the exact groups in the scene
            found_rig_groups = rig_joint_groups.intersection(scene_transforms)

            if found_rig_groups:
                print(f"[ManyAnims]  Found special rig joint group(s): {list(found_rig_groups)} → Skipping ClearAndRemoveCastNotetracks()")
            else:
                try:
                    CoDMayaTools.ClearAndRemoveCastNotetracks("xanim")
                    print("[ManyAnims]  Cleared and removed CAST notetracks.")
                except Exception as e:
                    print(f"[ManyAnims]  Failed to clear CAST notetracks: {e}")

        finally:
            cmds.window = _original_window
            update_progress_bar(progress_control, idx)

    # --- Close progress bar
    close_progress_bar()
    print(f"[ManyAnims]  Processed {len(files_to_process)} CAST animation(s).")

    # --- Reset scene to default
    try:
        castplugin.utilityClearAnimation()
        print("[ManyAnims] Scene cleared after CAST export.")
    except Exception as e:
        print(f"[ManyAnims]  Scene reset failed after CAST export: {e}")

    # --- Reset mode checkboxes
    cmds.menuItem(treyarch_checkbox, edit=True, checkBox=False)
    cmds.menuItem(iw_sh_checkbox, edit=True, checkBox=False)
    print("[ManyAnims] Reset Treyarch/IW-SH checkboxes after CAST export.")
    reset_export_selected_mode()


def reset_export_selected_mode():
    global export_selected_only

    export_selected_only = False

    if cmds.menuItem("exportSelectedMenuItem", exists=True):
        cmds.menuItem("exportSelectedMenuItem", edit=True, checkBox=False)

    print("[ManyAnims] Export Selected Joints mode reset.")

    
def create_menu():
    global treyarch_checkbox, iw_sh_checkbox
    global select_normal_joints_button, select_ads_joints_button

    if cmds.menu("manyAnimsMenu", exists=True):
        cmds.deleteUI("manyAnimsMenu", menu=True)

    cmds.menu("manyAnimsMenu", label="ManyAnims", parent="MayaWindow")
    cmds.menuItem(divider=True)
    cmds.menuItem(label="Import", command=select_anim_files_dialog)
    cmds.menuItem(label="Export", command=set_export_path)
    cmds.menuItem(divider=True)
    treyarch_checkbox = cmds.menuItem(label="Export Treyarch", checkBox=False, command=on_treyarch_checked)
    iw_sh_checkbox = cmds.menuItem(label="Export IW/SH", checkBox=False, command=on_iw_sh_checked)
    global export_selected_menu_item

    export_selected_menu_item = cmds.menuItem(
        "exportSelectedMenuItem",
        label="Export Selected Joints",
        checkBox=False,
        enable=False,  # start disabled
        command=toggle_export_selected_only
    )
    #select_normal_joints_button = cmds.menuItem(label="Select Normal Joints", command=select_normal_joints)
    #select_ads_joints_button = cmds.menuItem(label="Select ADS Joints", command=select_ads_joints)
    cmds.menuItem(divider=True)

    cmds.menuItem(subMenu=True, label="Settings", tearOff=False)
    cmds.menuItem(label="Set Game Prefix...", command=set_game_prefix)
    cmds.menuItem(label="Set Namespace...", command=open_namespace_dialog)
    cmds.menuItem(divider=True)
    cmds.menuItem("cod4ExportMenuItem", label="Export .xanim_export", checkBox=export_cod4, command=toggle_cod4_export)
    cmds.menuItem("bo3ExportMenuItem", label="Export .xanim_bin", checkBox=export_bo3, command=toggle_bo3_export)
    cmds.menuItem(divider=True)
    cmds.menuItem("useCastMenuItem", label="Import .CAST", checkBox=use_cast, command=toggle_use_cast)
    cmds.menuItem("useSEModeMenuItem", label="Import .SE", checkBox=use_se_mode, command=toggle_se_mode)
    cmds.menuItem(divider=True)
    cmds.menuItem(label="Set Import Location...", command=lambda *args: set_import_location())
    cmds.menuItem(label="Set Export Location...", command=lambda *args: set_export_location())
    cmds.menuItem(divider=True)
    cmds.menuItem("nameRemapMenuItem",
                label="Anim Auto Rename",
                checkBox=use_name_remap,
                command=toggle_name_remap)

    cmds.setParent("manyAnimsMenu", menu=True)
    cmds.menuItem(label="About", command=show_about_dialog)

    toggle_ui_elements(False)
    # --- Sync UI with saved settings on first load ---
    load_settings()

create_menu()