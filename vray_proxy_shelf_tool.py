from maya import cmds, mel
import os

selection = cmds.ls(selection=True, long=False) or []
default_name = selection[0].split("|")[-1].replace(":", "_") if selection else "proxy"
folder = os.path.join(cmds.workspace(query=True, rootDirectory=True), "assets")
os.makedirs(folder, exist_ok=True)
ui = {}


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

    if os.path.exists(xml):
        os.remove(xml)

    proxy = mel.eval(
        'vrayCreateProxy -exportType 1 -previewFaces 10000 '
        '-dir "{}" -fname "{}" -overwrite '
        '-createProxyNode -newProxyNode -node "vrayProxy";'.format(
            folder, filename
        )
    )

    if isinstance(proxy, (list, tuple)):
        proxy = proxy[0]

    proxy = (cmds.listRelatives(proxy, shapes=True, fullPath=True) or [proxy])[0]

    mel.eval(
        'vrayExportProxyRules "{}" "{}";'.format(
            proxy, xml.replace("\\", "/")
        )
    )
