import maya.cmds as cmds
import os
import sys
import maya.utils

# Global variables
anim_path = None
export_path = None
normal_joints = []
ads_joints = []
default_namespace = ""  # sloth rig is iw4
selected_anim_files = []
export_cod4 = True
export_bo3 = False

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

# UI functions
def add_menu_image_to_manyanims_menu(image_filename="ManyAnims_Logo.png"):
    image_path = os.path.join(cmds.internalVar(userPrefDir=True), image_filename)
    if os.path.exists(image_path):
        cmds.setParent("manyAnimsMenu", menu=True)
        cmds.menuItem(divider=True)
        cmds.menuItem(label="", image=image_path, enable=False)
    else:
        print("[ManyAnims] Image not found: %s" % image_path)

def select_anim_files_dialog(*args):
    global anim_path, selected_anim_files
    selected = cmds.fileDialog2(fileMode=4, dialogStyle=2, caption="Select SEAnim Files to Export", fileFilter="*.seanim")

    if selected:
        selected_anim_files = selected
        anim_path = os.path.dirname(selected[0])
        print("[ManyAnims] Animation path set to: %s" % anim_path)
        print("[ManyAnims] Selected %d file(s)" % len(selected_anim_files))
        cmds.confirmDialog(title="Animations Selected", message="Selected %d animation(s)." % len(selected_anim_files), button=["OK"])
        enable_ui_elements_if_paths_selected()
    else:
        selected_anim_files = []
        cmds.confirmDialog(title="No Selection", message="No animations selected.", button=["OK"])

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
            load_seanim_from_path(anim_path)
        else:
            cmds.confirmDialog(title="Error", message="Please select both Anim Path and Export Path first.", button=["OK"])

def on_iw_sh_checked(*args):
    if cmds.menuItem(iw_sh_checkbox, query=True, checkBox=True):
        cmds.menuItem(treyarch_checkbox, edit=True, checkBox=False)
        if anim_path and export_path:
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
    print("[ManyAnims] Setting current game to CoD4 (MW)...")
    CoDMayaTools.SetCurrentGame("CoD4")
    auto_rename_state = CoDMayaTools.QueryToggableOption("AutomaticRename")
    print("[ManyAnims] AutomaticRename before toggle (CoD4): %s" % auto_rename_state)
    if auto_rename_state:
        CoDMayaTools.SetToggableOption("AutomaticRename")
        print("[ManyAnims] AutomaticRename was enabled - now toggled OFF.")
    cmds.evalDeferred("CoDMayaTools.CreateMenu()")

def toggle_bo3_export(*args):
    global export_bo3, export_cod4
    export_bo3 = True
    export_cod4 = False
    cmds.menuItem("bo3ExportMenuItem", edit=True, checkBox=export_bo3)
    cmds.menuItem("cod4ExportMenuItem", edit=True, checkBox=export_cod4)
    print("[ManyAnims] Export for BO3: %s" % export_bo3)
    print("[ManyAnims] Setting current game to CoD12 (BO3)...")
    CoDMayaTools.SetCurrentGame("CoD12")
    auto_rename_state = CoDMayaTools.QueryToggableOption("AutomaticRename")
    print("[ManyAnims] AutomaticRename before toggle (BO3): %s" % auto_rename_state)
    if not auto_rename_state:
        CoDMayaTools.SetToggableOption("AutomaticRename")
        print("[ManyAnims] AutomaticRename was disabled - now toggled ON.")
    cmds.evalDeferred("CoDMayaTools.CreateMenu()")
    cmds.evalDeferred(lambda: force_update_codmaya_menu_checkbox("AutomaticRename", True))

def force_update_codmaya_menu_checkbox(item_name, desired_state):
    if cmds.menuItem(item_name, exists=True):
        cmds.menuItem(item_name, edit=True, checkBox=desired_state)
    

def create_progress_bar(numfiles):
    if cmds.control("ManyAsserts_progress", exists=True):
        cmds.deleteUI("ManyAsserts_progress")
    window = cmds.window("ManyAsserts_progress", title="Exporting Animations")
    cmds.columnLayout()
    progress = cmds.progressBar("ManyAsserts_progress", width=300, maxValue=numfiles)
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
    selected = cmds.fileDialog2(fileMode=3, dialogStyle=2, caption="Select Export Folder")
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
            load_seanim_from_path(anim_path)
        else:
            cmds.confirmDialog(title="Error", message="Please select both Anim Path and Export Path first.", button=["OK"])

def load_seanim_from_path(anim_path):
    files_to_process = selected_anim_files or [os.path.join(anim_path, f) for f in os.listdir(anim_path) if f.endswith(".seanim")]
    if not files_to_process:
        cmds.confirmDialog(title="No Animations", message="No .seanim files to process.", button=["OK"])
        return

    progress_control = create_progress_bar(len(files_to_process))

    for idx, anim_file_path in enumerate(files_to_process, 1):
        anim_file = os.path.basename(anim_file_path)
        print("Loading animation file: %s" % anim_file_path)
        SEToolsPlugin.__load_seanim__(anim_file_path, scene_time=False, blend_anim=False)
        export_xanim_file(anim_file_path, export_path, method_type="treyarch" if cmds.menuItem(treyarch_checkbox, query=True, checkBox=True) else "iw/sh")
        update_progress_bar(progress_control, idx)

    close_progress_bar()
    print("Processed %d animation(s)." % len(files_to_process))

        # Reset the scene after all animations are processed
    if hasattr(SEToolsPlugin, '__scene_resetanim__'):
        print("[ManyAnims] Resetting scene after export...")
        SEToolsPlugin.__scene_resetanim__()
    else:
        print("[ManyAnims] Warning: __scene_resetanim__ not found in SEToolsPlugin")



original_save_reminder = CoDMayaTools.SaveReminder

# Define your modified SaveReminder function
def modified_save_reminder(allow_unsaved=True):

    return True

def export_xanim_file(input_file_path, output_directory, method_type="treyarch"):
    ext = ".xanim_export" if export_cod4 else ".xanim_bin" if export_bo3 else ".xanim_export"
    output_file_path = os.path.join(output_directory, os.path.basename(input_file_path).replace('.seanim', ext))
    print("Exporting to path: %s" % output_file_path)

    filename_lower = os.path.basename(input_file_path).lower()
    is_ads = "ads_up" in filename_lower or "ads_down" in filename_lower

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
    if method_type == "treyarch":
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

    original_show_window = cmds.showWindow
    try:
        cmds.showWindow = lambda *args, **kwargs: None
        CoDMayaTools.GeneralWindow_ExportSelected('xanim', exportingMultiple=False)
    finally:
        cmds.showWindow = original_show_window
        CoDMayaTools.ClearNotes('xanim')
        CoDMayaTools.SaveReminder = original_save_reminder
def modified_save_reminder(allow_unsaved=True):
    return True




import os
import maya.cmds as cmds

def show_about_dialog(*args):
    # Clean up any existing window
    if cmds.window("manyanimsAboutWindow", exists=True):
        cmds.deleteUI("manyanimsAboutWindow")
    try:
        if cmds.windowPref("manyanimsAboutWindow", exists=True):
            cmds.windowPref("manyanimsAboutWindow", remove=True)
    except:
        pass

    # Create fixed-size, close-only window
    window = cmds.window("manyanimsAboutWindow",
                         title="About ManyAnims",
                         sizeable=False,
                         minimizeButton=False,
                         maximizeButton=False,
                         widthHeight=(400, 225))

    form = cmds.formLayout()

    # Main vertical layout
    main_col = cmds.columnLayout(adjustableColumn=True, rowSpacing=8)

    # Title section
    cmds.text(label="ManyAnims Tool for Maya", font="boldLabelFont", align="center", parent=main_col)
    cmds.text(label="Batch Animation Exporter", align="center", parent=main_col)
    cmds.text(label="Created by elfenliedtopfan5 for Sloth", align="center", parent=main_col)
    cmds.separator(style="in", height=10, parent=main_col)

    # Instructions frame
    frame = cmds.frameLayout(label="ChangeLog:", collapsable=False, borderStyle="etchedIn", marginWidth=10, marginHeight=10)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
    cmds.text(label="- Version 1.0.1 - UI changes", align="left")
    cmds.text(label="- Version 1.0.0 - Initial release", align="left")
    cmds.setParent("..")  # columnLayout
    cmds.setParent("..")  # frameLayout

    cmds.separator(style="in", height=10, parent=main_col)

    # OK Button at bottom
    button_row = cmds.rowLayout(numberOfColumns=1, adjustableColumn=1, height=40, parent=main_col)
    cmds.button(label="OK", height=30, width=100, command=lambda x: cmds.deleteUI("manyanimsAboutWindow"))
    cmds.setParent("..")  # rowLayout

    cmds.setParent(form)
    cmds.formLayout(form, edit=True,
                    attachForm=[
                        (main_col, 'top', 10),
                        (main_col, 'left', 10),
                        (main_col, 'right', 10),
                        (main_col, 'bottom', 10)
                    ])

    cmds.showWindow(window)






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
    cmds.menuItem("cod4ExportMenuItem", label="Export .xanim_export", checkBox=export_cod4, command=toggle_cod4_export)
    cmds.menuItem("bo3ExportMenuItem", label="Export .xanim_bin", checkBox=export_bo3, command=toggle_bo3_export)
    cmds.menuItem(label="Set Namespace...", command=open_namespace_dialog)
    cmds.setParent("manyAnimsMenu", menu=True)
    cmds.menuItem(label="About", command=show_about_dialog)

    toggle_ui_elements(False)

create_menu()