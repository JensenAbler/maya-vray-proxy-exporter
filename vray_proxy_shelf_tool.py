from maya import cmds, mel
import os

selection = cmds.ls(selection=True, long=True, objectsOnly=True) or []
default_name = selection[0].split("|")[-1].replace(":", "_") if selection else "proxy"
folder = os.path.join(cmds.workspace(query=True, rootDirectory=True), "assets")
os.makedirs(folder, exist_ok=True)
ui = {}


def assigned_materials(nodes):
    materials = []
    for node in nodes:
        shapes = [node]
        if cmds.nodeType(node) == "transform":
            shapes = cmds.listRelatives(
                node, allDescendents=True, shapes=True, fullPath=True
            ) or []
        for shape in shapes:
            for shading_group in cmds.listConnections(
                shape, type="shadingEngine"
            ) or []:
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

    path = os.path.join(folder, filename)
    xml = os.path.splitext(path)[0] + ".xml"
    folder = folder.replace("\\", "/")
    materials = assigned_materials(selection)

    mel.eval(
        'vrayCreateProxy -exportType 1 -previewFaces 10000 '
        '-dir "{}" -fname "{}" -overwrite;'.format(
            folder, filename
        )
    )

    cmds.select(clear=True)
    proxy = mel.eval(
        'vrayCreateProxy -existing -dir "{}" '
        '-createProxyNode -newProxyNode -node "vrayProxy";'.format(
            path.replace("\\", "/")
        )
    )

    if isinstance(proxy, (list, tuple)):
        proxy = proxy[0]

    children = cmds.listRelatives(proxy, children=True, fullPath=True) or []
    proxy = next(node for node in children if cmds.nodeType(node) == "VRayProxy")

    for index, material in enumerate(materials):
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

    if os.path.exists(xml):
        os.remove(xml)

    mel.eval(
        'vrayExportProxyRules "{}" "{}";'.format(
            proxy, xml.replace("\\", "/")
        )
    )

    cmds.select(selection, replace=True)
