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
    "export_location": ""
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

    # --- If the menu already exists, update checkboxes visually ---
    if cmds.menuItem("useCastMenuItem", exists=True):
        cmds.menuItem("useCastMenuItem", edit=True, checkBox=use_cast)
    if cmds.menuItem("useSEModeMenuItem", exists=True):
        cmds.menuItem("useSEModeMenuItem", edit=True, checkBox=use_se_mode)
    if cmds.menuItem("cod4ExportMenuItem", exists=True):
        cmds.menuItem("cod4ExportMenuItem", edit=True, checkBox=export_cod4)
    if cmds.menuItem("bo3ExportMenuItem", exists=True):
        cmds.menuItem("bo3ExportMenuItem", edit=True, checkBox=export_bo3)


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

    # Switch filter/caption depending on Use CAST toggle
    file_filter = "*.cast" if use_cast else "*.seanim"
    caption = "Select CAST Files to Export" if use_cast else "Select SEAnim Files to Export"

    start_dir = settings.get("import_location", "")
    if not start_dir or not os.path.exists(start_dir):
        start_dir = cmds.workspace(q=True, rd=True)  # fallback to current project root
    selected = cmds.fileDialog2(fileMode=4, dialogStyle=2, caption=caption,
                                fileFilter=file_filter, startingDirectory=start_dir)

    # Save directory if chosen
    if selected:
        settings["import_location"] = os.path.dirname(selected[0])
        save_settings()

    if selected:
        selected_anim_files = selected
        anim_path = os.path.dirname(selected[0])
        print("[ManyAnims] Animation path set to: %s" % anim_path)
        print("[ManyAnims] Selected %d file(s)" % len(selected_anim_files))
        cmds.confirmDialog(
            title="Animations Selected",
            message="Selected %d animation(s)." % len(selected_anim_files),
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
        settings["export_location"] = export_path
        save_settings()
    if selected:
        export_path = selected[0]
        cmds.confirmDialog(title="Export Path Selected", message="Export Path: " + export_path, button=["OK"])
        enable_ui_elements_if_paths_selected()

def enable_ui_elements_if_paths_selected():
    global anim_path, export_path
    if anim_path and export_path:
        toggle_ui_elements(True)

def toggle_ui_elements(enable):
    cmds.menuItem(treyarch_checkbox, edit=True, enable=enable)
    cmds.menuItem(iw_sh_checkbox, edit=True, enable=enable)
    cmds.menuItem(select_normal_joints_button, edit=True, enable=enable)
    cmds.menuItem(select_ads_joints_button, edit=True, enable=enable)

def trigger_export_if_all_selected():
    if normal_joints and ads_joints:
        if anim_path and export_path:
            if use_cast:
                load_cast_from_path(anim_path)
            else:
                load_seanim_from_path(anim_path)
        else:
            cmds.confirmDialog(title="Error", message="Please select both Anim Path and Export Path first.", button=["OK"])


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

        export_xanim_file(
            anim_file_path,
            export_path,
            method_type="treyarch" if cmds.menuItem(treyarch_checkbox, query=True, checkBox=True) else "iw/sh"
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


original_save_reminder = CoDMayaTools.SaveReminder

def modified_save_reminder(allow_unsaved=True):
    return True

def export_xanim_file(input_file_path, output_directory, method_type="treyarch"):
    ext = ".xanim_export" if export_cod4 else ".xanim_bin" if export_bo3 else ".xanim_export"
    output_file_path = os.path.join(output_directory, os.path.basename(input_file_path).replace('.seanim', ext))
    print("Exporting to path: %s" % output_file_path)

    filename_lower = os.path.basename(input_file_path).lower()
    is_ads = "ads_up" in filename_lower or "ads_down" in filename_lower

    # --- Joint selection logic ---
    if method_type == "manual":
        if is_ads:
            if ads_joints:
                cmds.select(ads_joints)
            else:
                cmds.confirmDialog(title="Error", message="ADS joints are not selected!", button=["OK"])
                return
        else:
            if normal_joints:
                cmds.select(normal_joints)
            else:
                cmds.confirmDialog(title="Error", message="Normal joints are not selected!", button=["OK"])
                return
    elif method_type == "treyarch":
        if is_ads:
            cmds.select("%s:tag_view" % default_namespace, "%s:tag_torso" % default_namespace)
        else:
            cmds.select("%s:tag_torso" % default_namespace, "%s:tag_cambone" % default_namespace, hierarchy=True)
    elif method_type == "iw/sh":
        if is_ads:
            if cmds.objExists("%s:tag_ads" % default_namespace):
                cmds.select("%s:tag_view" % default_namespace, "%s:tag_ads" % default_namespace)
            else:
                cmds.confirmDialog(title="Error", message="ADS joints ('%s:tag_ads') not found!" % default_namespace, button=["OK"])
                return
        else:
            if cmds.objExists("%s:tag_ads" % default_namespace) and cmds.objExists("%s:tag_cambone" % default_namespace):
                cmds.select("%s:tag_ads" % default_namespace, "%s:tag_cambone" % default_namespace, hierarchy=True)
            else:
                cmds.confirmDialog(title="Error", message="Required joints not found in namespace '%s'!" % default_namespace, button=["OK"])
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

    # Create window with fixed size and close button only
    window = cmds.window("manyanimsAboutWindow", title="About ManyAnims", sizeable=False, minimizeButton=False, maximizeButton=False)

    form = cmds.formLayout()

    # Title section
    title_col = cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    cmds.text(label="ManyAnims Tool for Maya", font="boldLabelFont", align="center")
    cmds.text(label="Batch Animation Exporter", align="center")
    cmds.text(label="Created by elfenliedtopfan5 for Sloth", align="center")
    cmds.separator(style="in", height=10)
    cmds.setParent(form)

    # Changelog section
    frame = cmds.frameLayout(label="ChangeLog:", collapsable=False, marginWidth=5, marginHeight=5)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    cmds.text(label="Version 1.1.0: Cast Support, UI Changes", align="center")
    cmds.text(label="Version 1.0.0: Initial release", align="center")
    cmds.setParent("..")  # columnLayout
    cmds.setParent("..")  # frameLayout

    # Spacer and OK button
    bottom_sep = cmds.separator(style="in", height=5)
    button_row = cmds.rowLayout(numberOfColumns=1, height=40, adjustableColumn=1)
    cmds.button(label="OK", height=30, width=100, command=lambda x: cmds.deleteUI("manyanimsAboutWindow"))
    cmds.setParent(form)

    # Attach layout elements
    cmds.formLayout(form, edit=True,
        attachForm=[
            (title_col, 'top', 10), (title_col, 'left', 10), (title_col, 'right', 10),
            (frame, 'left', 10), (frame, 'right', 10),
            (bottom_sep, 'left', 10), (bottom_sep, 'right', 10),
            (button_row, 'left', 0), (button_row, 'right', 0), (button_row, 'bottom', 10)
        ],
        attachControl=[
            (frame, 'top', 10, title_col),
            (bottom_sep, 'top', 10, frame),
            (button_row, 'top', 10, bottom_sep)
        ]
    )

    # Show and fix window size
    cmds.showWindow(window)
    cmds.window(window, edit=True, widthHeight=(450, 250))  

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
        output_file_path = os.path.join(export_path, cast_file.replace(".cast", ext))
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
        method_type = "treyarch" if cmds.menuItem(treyarch_checkbox, query=True, checkBox=True) else "iw/sh"
        fname = cast_file.lower()
        is_ads = "ads_up" in fname or "ads_down" in fname

        # --- Joint selection
        try:
            if method_type == "treyarch":
                if is_ads:
                    cmds.select(f"{default_namespace}:tag_view", f"{default_namespace}:tag_torso")
                else:
                    cmds.select(f"{default_namespace}:tag_torso", f"{default_namespace}:tag_cambone", hierarchy=True)
            elif method_type == "iw/sh":
                if is_ads:
                    if cmds.objExists(f"{default_namespace}:tag_ads"):
                        cmds.select(f"{default_namespace}:tag_view", f"{default_namespace}:tag_ads")
                    else:
                        cmds.confirmDialog(title="Error",
                                           message=f"ADS joint ('{default_namespace}:tag_ads') not found!",
                                           button=["OK"])
                        continue
                else:
                    if cmds.objExists(f"{default_namespace}:tag_ads") and cmds.objExists(f"{default_namespace}:tag_cambone"):
                        cmds.select(f"{default_namespace}:tag_ads", f"{default_namespace}:tag_cambone", hierarchy=True)
                    else:
                        cmds.confirmDialog(title="Error",
                                           message=f"Required joints not found in namespace '{default_namespace}'!",
                                           button=["OK"])
                        continue
        except Exception as e:
            cmds.warning(f"[ManyAnims]  Failed to select joints for {cast_file}: {e}")
            continue

        # --- Read notetracks
        try:
            CoDMayaTools.ReadNotetracks('xanim')
        except Exception as e:
            print(f"[ManyAnims]  Failed to read notetracks: {e}")



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
    cmds.menuItem(divider=True)
    select_normal_joints_button = cmds.menuItem(label="Select Normal Joints", command=select_normal_joints)
    select_ads_joints_button = cmds.menuItem(label="Select ADS Joints", command=select_ads_joints)
    cmds.menuItem(divider=True)

    cmds.menuItem(subMenu=True, label="Settings", tearOff=False)
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
    cmds.setParent("manyAnimsMenu", menu=True)
    cmds.menuItem(label="About", command=show_about_dialog)

    toggle_ui_elements(False)
    # --- Sync UI with saved settings on first load ---
    load_settings()

create_menu()