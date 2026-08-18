from maya import cmds, mel
import os
import re

selection = cmds.ls(selection=True, long=True, objectsOnly=True) or []
scene_name = os.path.splitext(os.path.basename(cmds.file(query=True, sceneName=True)))[0]
scene_version_match = re.search(r"(?i)_v(\d+)$", scene_name)
if not scene_version_match:
    cmds.error("The current Maya scene filename has no version token such as v001.")
scene_version = "v" + scene_version_match.group(1)
base_name = selection[0].split("|")[-1].replace(":", "_") if selection else "proxy"
default_name = base_name + "_" + scene_version
folder = os.path.join(cmds.workspace(query=True, rootDirectory=True), "assets")
os.makedirs(folder, exist_ok=True)
ui = {}


def apply_scene_version(filename):
    stem, extension = os.path.splitext(filename)
    if re.search(r"(?i)_v\d+$", stem):
        stem = re.sub(r"(?i)_v\d+$", "_" + scene_version, stem)
    else:
        stem += "_" + scene_version
    return stem + extension


def assigned_materials(nodes):
    shapes = []
    for node in nodes:
        found = [node] if cmds.nodeType(node) == "mesh" else cmds.ls(
            node, dagObjects=True, shapes=True, long=True, type="mesh"
        ) or []
        for shape in found:
            if shape not in shapes:
                shapes.append(shape)

    materials = []
    for shape in shapes:
        shading_groups = cmds.listConnections(
            shape + ".instObjGroups",
            source=False,
            destination=True,
            type="shadingEngine",
        ) or []
        for shading_group in shading_groups:
            connected = cmds.listConnections(
                shading_group + ".surfaceShader",
                source=True,
                destination=False,
            ) or []
            for material in connected:
                if material not in materials:
                    materials.append(material)
    return materials


def browse(*_):
    picked = cmds.fileDialog2(
        fileMode=1,
        fileFilter="V-Ray Mesh (*.vrmesh)",
        startingDirectory=folder,
    )
    if picked:
        cmds.textFieldButtonGrp(
            ui["name"], edit=True, text=os.path.basename(picked[0])
        )


def build_dialog():
    cmds.columnLayout(adjustableColumn=True, rowSpacing=8)
    ui["name"] = cmds.textFieldButtonGrp(
        label="Filename",
        text=default_name,
        buttonLabel="Browse",
        buttonCommand=browse,
    )
    cmds.rowLayout(numberOfColumns=2)
    cmds.button(
        label="Export",
        width=100,
        command=lambda *_: cmds.layoutDialog(
            dismiss=cmds.textFieldButtonGrp(ui["name"], query=True, text=True)
        ),
    )
    cmds.button(
        label="Cancel",
        width=100,
        command=lambda *_: cmds.layoutDialog(dismiss="Cancel"),
    )


filename = cmds.layoutDialog(title="Export V-Ray Proxy", ui=build_dialog)

if filename and filename not in ("Cancel", "dismiss"):
    filename = os.path.basename(filename.strip())
    if not filename.lower().endswith(".vrmesh"):
        filename += ".vrmesh"
    filename = apply_scene_version(filename)

    path = os.path.join(folder, filename)
    xml = os.path.splitext(path)[0] + ".xml"
    proxy_name = os.path.splitext(filename)[0] + "_proxy"
    folder = folder.replace("\\", "/")
    materials = assigned_materials(selection)
    if not materials:
        cmds.error("No materials were found on the selected geometry.")

    mel.eval(
        'vrayCreateProxy -exportType 1 -previewFaces 10000 '
        '-dir "{}" -fname "{}" -overwrite;'.format(
            folder, filename
        )
    )

    cmds.select(clear=True)
    proxy = mel.eval(
        'vrayCreateProxy -existing -dir "{}" '
        '-createProxyNode -newProxyNode -node "{}";'.format(
            path.replace("\\", "/"), proxy_name
        )
    )

    if isinstance(proxy, (list, tuple)):
        proxy = proxy[0]

    children = cmds.listRelatives(proxy, children=True, fullPath=True) or []
    proxy = next(node for node in children if cmds.nodeType(node) == "VRayProxy")

    proxy_materials = {
        name[2:]
        for name in (cmds.vrayUpdateProxy(proxy, getObjectNames=True) or [])
        if name.startswith("s:")
    }
    matched_materials = [
        material for material in materials if material in proxy_materials
    ]
    if not matched_materials:
        cmds.error("No source material names matched the proxy shader sets.")

    for index, material in enumerate(matched_materials):
        cmds.setAttr(
            "{}.shadersCustom[{}].shadersCustomNames".format(proxy, index),
            material,
            type="string",
        )
        cmds.connectAttr(
            material + ".outColor",
            "{}.shadersCustom[{}].shadersCustomConnections".format(proxy, index),
            force=True,
        )

    complete_rules = 0
    for index in range(len(matched_materials)):
        pattern = cmds.getAttr(
            "{}.shadersCustom[{}].shadersCustomNames".format(proxy, index)
        )
        connection = cmds.listConnections(
            "{}.shadersCustom[{}].shadersCustomConnections".format(proxy, index),
            source=True,
            destination=False,
        ) or []
        if pattern and connection:
            complete_rules += 1
    if not complete_rules:
        cmds.error("No complete material override rules were created.")

    if os.path.exists(xml):
        os.remove(xml)

    mel.eval(
        'vrayExportProxyRules "{}" "{}";'.format(
            proxy, xml.replace("\\", "/")
        )
    )

    cmds.select(selection, replace=True)
