import json
import adsk.core, adsk.fusion, adsk.cam, traceback, math, random
import os
from ...lib import fusion360utils as futil
from ... import config

app = adsk.core.Application.get()
ui = app.userInterface

# TODO ********************* Change these names *********************
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_palette_send'
CMD_NAME = 'Copy Scale Rotate Translate Rotate'
CMD_Description = 'Copy Scale Rotate Translate Rotate to create patterns/fractals of bodies'
IS_PROMOTED = False

# Using "global" variables by referencing values from /config.py
PALETTE_ID = config.sample_palette_id

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidCreatePanel'
COMMAND_BESIDE_ID = 'MirrorCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []
global scale_transform
global internal_rotation_transform
global translation_transform
global external_rotation_transform


# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Add command created handler. The function passed here will be executed when the command is executed.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

#    allTooolbarPanels = workspace.toolbarPanels
#    for toolbarPanel in allTooolbarPanels:
#        futil.log(f'toolbar panel: {toolbarPanel.name}')

#    allWorkspaceTabs = workspace.toolbarTabs
#    for workspaceTab in allWorkspaceTabs:
#        futil.log(f'workspace tab: {workspaceTab.name}')
#        if (workspaceTab.name == 'SOLID'):
#            for toolbarPanel in workspaceTab.toolbarPanels:
#                futil.log(f'toolbar panel: {toolbarPanel.name}')  
#                if (toolbarPanel.name == 'Create'):
#                    for toolbarPanelControls in toolbarPanel.controls:
#                        futil.log(f'toolbar panel controls: {toolbarPanelControls}')  
#                    for toolbarPanelID in toolbarPanel.id:
#                        futil.log(f'toolbar panel controls: {toolbarPanelID}')  

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Event handler that is called when the user clicks the command button in the UI.
# To have a dialog, you create the desired command inputs here. If you don't need
# a dialog, don't create any inputs and the execute event will be immediately fired.
# You also need to connect to any command related events here.
def command_created(args: adsk.core.CommandCreatedEventArgs):
#    global update_preview_flag
    global preview_interference_flag
    global scale_transform
    global internal_rotation_transform
    global translation_transform
    global external_rotation_transform
    global activeTab
    global oldTab
    global tabCmdInputCopy 
    global tabCmdInputScale
    global tabCmdInputInternalRotation
    global tabCmdInputTranslation
    global tabCmdInputExternalRotation
    global tabCmdInputPreview

    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # TODO Create the event handlers you will need for this instance of the command
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

    # Create the user interface for your command by adding different inputs to the CommandInputs object
    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    reset_button_icons = os.path.join(ICON_FOLDER, 'reset_button')
    interference_button_icons = os.path.join(ICON_FOLDER, 'interference_button')
    inputs = args.command.commandInputs

#    update_preview_flag = False
    preview_interference_flag = False

    # TODO ******************************** Define your UI Here ********************************
    
    # Create a tab for Copy commands
    tabCmdInputCopy = inputs.addTabCommandInput('tab_copy', 'Copy')
    tabCopyChildInputs = tabCmdInputCopy.children
    activeTab = 'tab_copy'
    oldTab = 'tab_copy'
    # Create a tab for Scale commands
    tabCmdInputScale = inputs.addTabCommandInput('tab_scale', 'Scale')
    tabScaleChildInputs = tabCmdInputScale.children
    # Create a tab for Internal Rotation commands
    tabCmdInputInternalRotation = inputs.addTabCommandInput('tab_internal_rotation', 'Internal Rotation')
    tabInternalRotationChildInputs = tabCmdInputInternalRotation.children
    # Create a tab for Translation commands
    tabCmdInputTranslation = inputs.addTabCommandInput('tab_translation', 'Translation')
    tabTranslationChildInputs = tabCmdInputTranslation.children
    # Create a tab for External Rotation commands
    tabCmdInputExternalRotation = inputs.addTabCommandInput('tab_external_rotation', 'External Rotation')
    tabExternalRotationChildInputs = tabCmdInputExternalRotation.children
    # Create a tab for Preview commands
    tabCmdInputPreview = inputs.addTabCommandInput('tab_preview', 'Preview')
    tabPreviewChildInputs = tabCmdInputPreview.children

    
## COPY
    # Create a read only textbox input.
    tabCopyChildInputs.addTextBoxCommandInput('readonly_textBox', 'Copy Instructions', 'Choose which bodies to copy, as well as the number of copies to make.  Note that increasing the number of copies may consume too much memory.', 3, True)
    
    # Create a selection input.
    selectionInput = tabCopyChildInputs.addSelectionInput('selection', 'Select', 'Select bodies to copy')
    selectionInput.setSelectionLimits(0)
    selectionInput.addSelectionFilter('Bodies')

    # Create integer slider input with one slider.
    numCopiesSlider = tabCopyChildInputs.addIntegerSliderCommandInput('num_copies', 'number of copies', 1, 100);
    numCopiesSlider.valueOne = 1

    # Create radio button group input.
    copyRadioButtonGroup = tabCopyChildInputs.addRadioButtonGroupCommandInput('copyRadioButtonGroup', 'Copy Options')
    copyRadioButtonItems = copyRadioButtonGroup.listItems
    copyRadioButtonItems.add("copy and remove original bodies", True)
    copyRadioButtonItems.add("copy and keep original bodies", False)
    copyRadioButtonItems.add("keep original bodies", False)
    copyRadioButtonItems.add("remove original bodies", False)

    # Create a checkbox.
    newComponentBoolean = tabCopyChildInputs.addBoolValueInput('create new components', 'create new component for each body', True, "", True)
    applyRecursivelyBoolean = tabCopyChildInputs.addBoolValueInput('apply transformations recursively', 'apply transformations recursively to newly generated bodies', True, "", True)


## SCALE
    # Create group input.
    scaleGroupCmdInput = tabScaleChildInputs.addGroupCommandInput('scale', 'Scale Object')
    scaleGroupCmdInput.isExpanded = True
    scaleGroupCmdInput.isEnabledCheckBoxDisplayed = True
    scaleGroupChildInputs = scaleGroupCmdInput.children
    # Create radio button group input.
    scaleCompoundRadioButtonGroup = scaleGroupChildInputs.addRadioButtonGroupCommandInput('scaleCompoundRadioButtonGroup', 'Scale Options')
    scaleCompoundRadioButtonItems = scaleCompoundRadioButtonGroup.listItems
    scaleCompoundRadioButtonItems.add("constant scale for all bodies", False)
    scaleCompoundRadioButtonItems.add("compound scale for each copy", True)
    # Create a transform input.
    scale_transform = adsk.core.Matrix3D.create()
    # Create radio button group input.
    scaleEquationRadioButtonGroup = scaleGroupChildInputs.addRadioButtonGroupCommandInput('scaleEquationRadioButtonGroup', 'Scale Equation Options')
    scaleEquationRadioButtonItems = scaleEquationRadioButtonGroup.listItems
    scaleEquationRadioButtonItems.add("scale uniformly", True)
    scaleEquationRadioButtonItems.add("scale X,Y,Z axes separately", False)
    # Create texbox value inputs.
    scaleValueInput = scaleGroupChildInputs.addTextBoxCommandInput('scale_value', 'Scale Ratio', '1.0', 1, False)
    scaleValueInput.isEnabled = True
    scaleValueInput.isVisible = True
    scaleValueInputX = scaleGroupChildInputs.addTextBoxCommandInput('scale_value_x', 'Scale Ratio X-axis', '1.0', 1, False)
    scaleValueInputX.isEnabled = False
    scaleValueInputX.isVisible = False    
    scaleValueInputY = scaleGroupChildInputs.addTextBoxCommandInput('scale_value_y', 'Scale Ratio Y-axis', '1.0', 1, False)
    scaleValueInputY.isEnabled = False
    scaleValueInputY.isVisible = False
    scaleValueInputZ = scaleGroupChildInputs.addTextBoxCommandInput('scale_value_z', 'Scale Ratio Z-axis', '1.0', 1, False)
    scaleValueInputZ.isEnabled = False
    scaleValueInputZ.isVisible = False
    # Create integer slider input.
    scaleRandomization = scaleGroupChildInputs.addIntegerSliderCommandInput('scale_randomization', 'Scale Randomization %', 0, 100, False)
    scaleRandomization.isEnabled = True
    scaleRandomization.isVisible = True
    scaleRandomizationX = scaleGroupChildInputs.addIntegerSliderCommandInput('scale_randomization_x', 'Scale X Randomization %', 0, 100, False)
    scaleRandomizationX.isEnabled = False
    scaleRandomizationX.isVisible = False
    scaleRandomizationY = scaleGroupChildInputs.addIntegerSliderCommandInput('scale_randomization_y', 'Scale Y Randomization %', 0, 100, False)
    scaleRandomizationY.isEnabled = False
    scaleRandomizationY.isVisible = False
    scaleRandomizationZ = scaleGroupChildInputs.addIntegerSliderCommandInput('scale_randomization_z', 'Scale Z Randomization %', 0, 100, False)
    scaleRandomizationZ.isEnabled = False
    scaleRandomizationZ.isVisible = False

    # Create a reset button.
    scaleResetBoolean = scaleGroupChildInputs.addBoolValueInput('reset scale', 'Reset Scale Values', False, reset_button_icons, False)

## INTERNAL ROTATATION
    # Create group input.
    internalRotationGroupCmdInput = tabInternalRotationChildInputs.addGroupCommandInput('internal rotation', 'Internally Rotate')
    internalRotationGroupCmdInput.isExpanded = True
    internalRotationGroupCmdInput.isEnabledCheckBoxDisplayed = True
    internalRotationGroupChildInputs = internalRotationGroupCmdInput.children
    # Create radio button group input.
    internalRotationRadioButtonGroup = internalRotationGroupChildInputs.addRadioButtonGroupCommandInput('internalRotationRadioButtonGroup', 'Internal Rotation Options')
    internalRotationRadioButtonItems = internalRotationRadioButtonGroup.listItems
    internalRotationRadioButtonItems.add("constant angle for all bodies", True)
    internalRotationRadioButtonItems.add("compound angle for each copy", False)
    # Create a transform input.
    internal_rotation_transform = adsk.core.Matrix3D.create()
    internalRotationTriadOutput = internalRotationGroupChildInputs.addTriadCommandInput('internal_rotation_triad', internal_rotation_transform)
    internalRotationTriadOutput.hideAll()
    # Create integer slider input.
    internalRotationRandomization = internalRotationGroupChildInputs.addIntegerSliderCommandInput('internal_rotation_randomization', 'Internal Rotation Randomization (deg)', 0, 360, False)
    # Create a reset button.
    internalRotationResetBoolean = internalRotationGroupChildInputs.addBoolValueInput('reset internal rotation', 'Reset Internal Rotation Values', False, reset_button_icons, False)

## TRANSLATION
    # Create group input.
    translationGroupCmdInput = tabTranslationChildInputs.addGroupCommandInput('translation', 'Translate')
    translationGroupCmdInput.isExpanded = True
    translationGroupCmdInput.isEnabledCheckBoxDisplayed = True
    translationGroupChildInputs = translationGroupCmdInput.children
    # Create radio button group input.
    translationRadioButtonGroup = translationGroupChildInputs.addRadioButtonGroupCommandInput('translationRadioButtonGroup', 'Translation Options')
    translationRadioButtonItems = translationRadioButtonGroup.listItems
    translationRadioButtonItems.add("constant distance for all bodies", False)
    translationRadioButtonItems.add("compound distance for each copy", False)
    translationRadioButtonItems.add("compound distance and scale for each copy", True)
    # Create a transform input.
    translation_transform = adsk.core.Matrix3D.create()
    translationTriadOutput = translationGroupChildInputs.addTriadCommandInput('translation_triad', translation_transform)
    translationTriadOutput.hideAll()
    # Create integer slider input.
    translationRandomizationX = translationGroupChildInputs.addIntegerSliderCommandInput('translation_randomization_x', 'Translation X Randomization %', 0, 100, False)
    translationRandomizationY = translationGroupChildInputs.addIntegerSliderCommandInput('translation_randomization_y', 'Translation Y Randomization %', 0, 100, False)
    translationRandomizationZ = translationGroupChildInputs.addIntegerSliderCommandInput('translation_randomization_z', 'Translation Z Randomization %', 0, 100, False)
    # Create a reset button.
    translationResetBoolean = translationGroupChildInputs.addBoolValueInput('reset translation', 'Reset Translation Values', False, reset_button_icons, False)

## EXTERNAL ROTATATION
    # Create group input.
    externalRotationGroupCmdInput = tabExternalRotationChildInputs.addGroupCommandInput('external rotation', 'Externally Rotate')
    externalRotationGroupCmdInput.isExpanded = True
    externalRotationGroupCmdInput.isEnabledCheckBoxDisplayed = True
    externalRotationGroupChildInputs = externalRotationGroupCmdInput.children
    # Create radio button group input.
    externalRotationRadioButtonGroup = externalRotationGroupChildInputs.addRadioButtonGroupCommandInput('externalRotationRadioButtonGroup', 'External Rotation Options')
    externalRotationRadioButtonItems = externalRotationRadioButtonGroup.listItems
    externalRotationRadioButtonItems.add("constant angle for all bodies", True)
    externalRotationRadioButtonItems.add("compound angle for each copy", False)   
    # Create a transform input.
    external_rotation_transform = adsk.core.Matrix3D.create()
    externalRotationTriadOutput = externalRotationGroupChildInputs.addTriadCommandInput('external_rotation_triad', external_rotation_transform)
    externalRotationTriadOutput.hideAll()
    # Create integer slider input.
    externalRotationRandomization = externalRotationGroupChildInputs.addIntegerSliderCommandInput('external_rotation_randomization', 'External Rotation Randomization (deg)', 0, 360, False)
    # Create a reset button.
    externalRotationResetBoolean = externalRotationGroupChildInputs.addBoolValueInput('reset external rotation', 'Reset External Rotation Values', False, reset_button_icons, False)


## PREVIEW    
    # Preview Tab Instructions text input box
    tabPreviewChildInputs.addTextBoxCommandInput('preview_instructions', 'Preview Instructions', 'Enabling Preview will consume resources and will be applied to every input change.  Turn off preview when making multiple changes.', 3, True)

    previewGroupCmdInput = tabPreviewChildInputs.addGroupCommandInput('preview', 'Show Preview')
    previewGroupCmdInput.isExpanded = True
    previewGroupCmdInput.isEnabledCheckBoxDisplayed = True
    previewGroupChildInputs = previewGroupCmdInput.children

    # Create radio button group input.
    previewRadioButtonGroup = previewGroupChildInputs.addRadioButtonGroupCommandInput('previewRadioButtonGroup', 'Preview Options')
    previewRadioButtonItems = previewRadioButtonGroup.listItems
    previewRadioButtonItems.add("use actual bodies", True)
    previewRadioButtonItems.add("use cube as body", False)
    previewRadioButtonItems.add("use sphere as body", False)

    # Create a interference button.
    interferenceBoolean = previewGroupChildInputs.addBoolValueInput('preview interference', 'Show Interference', False, interference_button_icons, False)

## ALL
    # To create a numerical input with units, we need to get the current units and create a "ValueInput"
    # https://help.autodesk.com/view/fusion360/ENU/?contextId=ValueInput
#    users_current_units = app.activeProduct.unitsManager.defaultLengthUnits
#    default_value = adsk.core.ValueInput.createByString(f'1 {users_current_units}')
#    inputs.addValueInput('value_input', 'Value Message', users_current_units, default_value)


# This function will be called when the user hits the OK button in the command dialog
def command_execute(args: adsk.core.CommandEventArgs):
    futil.log(f'{CMD_NAME} Command Execute Event')
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    # General logging for debug
    futil.log(f'{CMD_NAME} Command Execute Event')

# This function will be called when the command needs to compute a new preview in the graphics window
def command_preview(args: adsk.core.CommandEventArgs):
#    global update_preview_flag
    global preview_interference_flag
    global scale_transform
    global internal_rotation_transform
    global translation_transform
    global external_rotation_transform

    inputs = args.command.commandInputs
    preview_input: adsk.core.GroupCommandInput = inputs.itemById('preview')
    show_preview_flag = preview_input.isEnabledCheckBoxChecked
    if (show_preview_flag == False):
        args.isValidResult = False
    else:
        futil.log(f'{CMD_NAME} Command Preview Event')
        design = adsk.fusion.Design.cast(app.activeProduct)
        # Get the root component of the active design.
        rootComp = design.rootComponent
        features = rootComp.features
        # Get the selection.
        selection = ui.activeSelections
        # Create a scales feature
        scaleFeats = rootComp.features.scaleFeatures
        # Create a move feature
        moveFeats = features.moveFeatures
        # Create remove feature
        removeFeats = features.removeFeatures

        num_copies = inputs.itemById('num_copies').valueOne

        do_scaling_flag = inputs.itemById('scale').isEnabledCheckBoxChecked
        do_internal_rotation_flag = inputs.itemById('internal rotation').isEnabledCheckBoxChecked
        do_translation_flag = inputs.itemById('translation').isEnabledCheckBoxChecked
        do_external_rotation_flag = inputs.itemById('external rotation').isEnabledCheckBoxChecked
        copy_radio_button: adsk.core.RadioButtonGroupCommandInput = inputs.itemById('copyRadioButtonGroup')
        do_copy_original_bodies = (copy_radio_button.selectedItem.name == 'copy and remove original bodies') or (copy_radio_button.selectedItem.name == 'copy and keep original bodies')
        do_remove_original_bodies = (copy_radio_button.selectedItem.name == 'copy and remove original bodies') or (copy_radio_button.selectedItem.name == 'remove original bodies')
        do_create_new_component_for_each_body = inputs.itemById('create new components').value
        do_apply_transformations_recursively = inputs.itemById('apply transformations recursively').value

        originalBodiesCollection = adsk.core.ObjectCollection.create()
        bodiesCollection = []

        previewRadioButtonGroupSelection = inputs.itemById('previewRadioButtonGroup').selectedItem.name
        if (previewRadioButtonGroupSelection == "use actual bodies"):
            # GRAB BODIES FROM SELECTION
            for selected_body_index in range(selection.count):
                # Get the first selected object.
                selectedObject = selection.item(selected_body_index).entity

                # Cast the selected object to a body.
                body = adsk.fusion.BRepBody.cast(selectedObject)

                # Check that the selected object is a body.
                if not body:
                    app.log('WARNING: selected object is not a body. skipping...  ')
                    ui.messageBox('The selected object is not a body', 'Not a Body')
                    # return
                else:
                    originalBodiesCollection.add(body)
                    app.log('  USING ' + body.name)
        else: 
            sample_dimension_size = 0.5
            if (previewRadioButtonGroupSelection == "use cube as body"):
                # Create a cube with a base edge length of sample_dimension_size 

                # Create a new sketch on the xy plane.
                sketches = rootComp.sketches;
                xyPlane = rootComp.xYConstructionPlane;
                sketch = sketches.add(xyPlane)

                # Get sketch lines
                sketchLines = sketch.sketchCurves.sketchLines

                # Create sketch rectangle
                startPoint = adsk.core.Point3D.create(0, 0, 0)
                endPoint = adsk.core.Point3D.create(sample_dimension_size, sample_dimension_size, 0)
                sketchLines.addTwoPointRectangle(startPoint, endPoint)
                
                # Get the profile defined by half of the circle.
                prof = sketch.profiles.item(0)

                # Create a simple extrusion of the profile
                extrudeFeat = rootComp.features.extrudeFeatures
                distance = adsk.core.ValueInput.createByReal(sample_dimension_size)

                # Create the extrusion.
                ext = extrudeFeat.addSimple(prof, distance, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)  
                body = ext.bodies[0]

            elif (previewRadioButtonGroupSelection == "use sphere as body"):
                # Create a new sketch on the xy plane.
                sketches = rootComp.sketches;
                xyPlane = rootComp.xYConstructionPlane;
                sketch = sketches.add(xyPlane)

                # Draw a circle.
                circles = sketch.sketchCurves.sketchCircles
                circle = circles.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), sample_dimension_size)
                
                # Draw a line to use as the axis of revolution.
                lines = sketch.sketchCurves.sketchLines
                axisLine = lines.addByTwoPoints(adsk.core.Point3D.create(-sample_dimension_size, 0, 0), adsk.core.Point3D.create(sample_dimension_size, 0, 0))

                # Get the profile defined by half of the circle.
                prof = sketch.profiles.item(0)

                # Create an revolution input to be able to define the input needed for a revolution
                # while specifying the profile and that a new component is to be created
                revolveFeat = rootComp.features.revolveFeatures
                revInput = revolveFeat.createInput(prof, axisLine, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)

                # Define that the extent is an angle of 2*pi to get a sphere
                angle = adsk.core.ValueInput.createByReal(2*math.pi)
                revInput.setAngleExtent(False, angle)

                # Create the extrusion.
                rev = revolveFeat.add(revInput)
                body = rev.bodies[0]
            

            if not body:
                app.log('WARNING: selected object is not a body. skipping...  ')
                ui.messageBox('The selected object is not a body', 'Not a Body')
                # return
            else:
                originalBodiesCollection.add(body)
    

        if (len(originalBodiesCollection) > 0):
            # Create centerpoint
            sketches = rootComp.sketches
            sketch = sketches.add(rootComp.xZConstructionPlane)
            centerPoint = adsk.core.Point3D.create(0, 0, 0)
            basePt = sketch.sketchPoints.item(0)

            cumulativeBodiesCollection = adsk.core.ObjectCollection.create()

            # COPY ORIGINAL BODIES
            # copy over original bodies and keep as copies
            if (do_copy_original_bodies):
                for selected_body_index in range(originalBodiesCollection.count):
                    app.log('copying iteration ' + str(0))
                    app.log('  original bodies collection count: ' + str(originalBodiesCollection.count))
                    bodiesCollection.append(adsk.core.ObjectCollection.create())
                    app.log('    copying body number ' + str(selected_body_index))
                    # Get the first selected object.
                    body = originalBodiesCollection.item(selected_body_index)
                    
                    # Copy the body.
                    copy = body.copyToComponent(rootComp)
                    copy.name = body.name + "_" + str(0)
                    app.log('  CREATED BODY: ' + copy.name + ' from original body ' + body.name)

                    # Add body to collection
                    bodiesCollection[0].add(copy)
                    cumulativeBodiesCollection.add(copy)
            else:
                bodiesCollection.append(adsk.core.ObjectCollection.create())

            for k in range(num_copies):
                app.log('copying iteration ' + str(k+1))
                app.log('  original bodies collection count: ' + str(originalBodiesCollection.count))
                bodiesCollection.append(adsk.core.ObjectCollection.create())

                for selected_body_index in range(originalBodiesCollection.count):
                    app.log('    copying body number ' + str(selected_body_index))
                    # Get the first selected object.

                    body = originalBodiesCollection.item(selected_body_index)
                    
                    # Copy the body.
                    copy = body.copyToComponent(rootComp)
                    copy.name = body.name + "_" + str(k+1)
                    app.log('  CREATED BODY: ' + copy.name + ' from original body ' + body.name)
                    app.log('  selection count: ' + str(selected_body_index))

                    bodiesCollection[k+1].add(copy)
                    cumulativeBodiesCollection.add(copy)
                    
                if (do_scaling_flag == True):
                    app.log('  SCALING: ' + ' copy ' + str(k+1) + ' body: ' + str(selected_body_index))
                    scale_equation_radio_button: adsk.core.RadioButtonGroupCommandInput = inputs.itemById('scaleEquationRadioButtonGroup')
                    scale_uniformly = (scale_equation_radio_button.selectedItem.name == 'scale uniformly')
                    scale_randomization = inputs.itemById('scale_randomization').valueOne
                    scale_randomization_x = inputs.itemById('scale_randomization_x').valueOne
                    scale_randomization_y = inputs.itemById('scale_randomization_y').valueOne
                    scale_randomization_z = inputs.itemById('scale_randomization_z').valueOne
                    if (scale_uniformly):
                        scale_value = eval(inputs.itemById('scale_value').text)
                        if (scale_value == 0):
                            app.log("     cannot scale by (" + str(scale_value) + ")")
                        else:
                            app.log("     scaling uniformly by (" + str(scale_value) + ")")
                            scale_transform = adsk.core.Matrix3D.create()
                            scale_transform.setCell(0, 0, scale_value)
                            scale_transform.setCell(1, 1, scale_value)
                            scale_transform.setCell(2, 2, scale_value)
                    else:
                    # Set the scale to be non-uniform
                        scale_value_x = eval(inputs.itemById('scale_value_x').text)
                        scale_value_y = eval(inputs.itemById('scale_value_y').text)
                        scale_value_z = eval(inputs.itemById('scale_value_z').text)
                        if ((scale_value_x == 0) or (scale_value_y == 0) or (scale_value_z == 0)):
                            app.log("     cannot scale by (" + str(scale_value_x) + ", " + str(scale_value_y) + ", " + str(scale_value_z) + ")")
                        else:
                            app.log("     scaling non-uniformly by (" + str(scale_value_x) + ", " + str(scale_value_y) + ", " + str(scale_value_z) + ")")
                            scale_transform = adsk.core.Matrix3D.create()
                            scale_transform.setCell(0, 0, scale_value_x)
                            scale_transform.setCell(1, 1, scale_value_y)
                            scale_transform.setCell(2, 2, scale_value_z)

                    scaleCompoundRadioButtonGroupSelection = inputs.itemById('scaleCompoundRadioButtonGroup').selectedItem.name
                    if (scaleCompoundRadioButtonGroupSelection == "constant scale for all bodies"):
                        apply_scale_transform = scale_transform
                    elif (scaleCompoundRadioButtonGroupSelection == "compound scale for each copy"):
                        apply_scale_transform = compound_transform(scale_transform, k+1)
                    app.log('    with transformation array: ' + str(apply_scale_transform.asArray()))
                    xScale = apply_scale_transform.getCell(0, 0)
                    yScale = apply_scale_transform.getCell(1, 1)
                    zScale = apply_scale_transform.getCell(2, 2)
                    xScaleRandomization = 1
                    yScaleRandomization = 1
                    zScaleRandomization = 1
                    if (scale_uniformly and (scale_randomization > 0)):
                        uniformScale = (1 + random.uniform(-1.0, 1.0) * scale_randomization / 100)
                        xScaleRandomization = uniformScale
                        yScaleRandomization = uniformScale
                        zScaleRandomization = uniformScale
                    elif (not scale_uniformly):
                        if (scale_randomization_x > 0):
                            xScaleRandomization = (1 + random.uniform(-1.0, 1.0) * scale_randomization_x / 100)
                        if (scale_randomization_y > 0):
                            yScaleRandomization = (1 + random.uniform(-1.0, 1.0) * scale_randomization_y / 100)
                        if (scale_randomization_z > 0):
                            zScaleRandomization = (1 + random.uniform(-1.0, 1.0) * scale_randomization_z / 100)
                    xScale = xScale * xScaleRandomization
                    yScale = yScale * yScaleRandomization
                    zScale = zScale * zScaleRandomization
                    if ((xScale == 1.0) and (yScale == 1.0) and (zScale == 1.0)):
                        app.log('    which is identity matrix, so not performing matrix transformation')
                    else:
                        if (do_apply_transformations_recursively == True):
                            app.log('    !!!!!!! applying transformations recursively for scaling')
                            scaleInput = scaleFeats.createInput(cumulativeBodiesCollection, basePt, adsk.core.ValueInput.createByReal(1.0))
                        else:
                            scaleInput = scaleFeats.createInput(bodiesCollection[k+1], basePt, adsk.core.ValueInput.createByReal(1.0))
                        scaleInput.setToNonUniform(adsk.core.ValueInput.createByReal(xScale), adsk.core.ValueInput.createByReal(yScale), adsk.core.ValueInput.createByReal(zScale))
                        scaleFeats.add(scaleInput)        

                if (do_internal_rotation_flag == True):
                    app.log('  INTERNALLY ROTATING: ' + ' copy ' + str(k+1) + ' body: ' + str(selected_body_index))
                    internalRotationRadioButtonGroupSelection = inputs.itemById('internalRotationRadioButtonGroup').selectedItem.name
                    if (internalRotationRadioButtonGroupSelection == "constant angle for all bodies"):
                        apply_internal_rotation_transform = internal_rotation_transform
                    elif (internalRotationRadioButtonGroupSelection == "compound angle for each copy"):
                        apply_internal_rotation_transform = compound_transform(internal_rotation_transform, k+1)

                    internal_rotation_randomization = inputs.itemById('internal_rotation_randomization').valueOne
                    if (internal_rotation_randomization > 0):
                        random_internal_rotation_transform = adsk.core.Matrix3D.create()
                        random_internal_rotation_transform.setToRotation((math.pi / 180.0) * random.uniform(0,internal_rotation_randomization), get_random_vector(), centerPoint)
                        apply_internal_rotation_transform.transformBy(random_internal_rotation_transform)

                    app.log('    with transformation array: ' + str(apply_internal_rotation_transform.asArray()))
                    if (apply_internal_rotation_transform.isEqualTo(adsk.core.Matrix3D.create())):
                        app.log('    which is identity matrix, so not performing matrix transformation')
                    else:
                        if (do_apply_transformations_recursively == True):
                            app.log('    !!!!!!! applying transformations recursively for internal rotation')
                            internal_rotateFeatureInput = moveFeats.createInput(cumulativeBodiesCollection, apply_internal_rotation_transform)
                        else:
                            internal_rotateFeatureInput = moveFeats.createInput(bodiesCollection[k+1], apply_internal_rotation_transform)
                        moveFeats.add(internal_rotateFeatureInput)        


                if (do_translation_flag == True):
                    app.log('  TRANSLATING: ' + ' copy ' + str(k+1) + ' body: ' + str(selected_body_index))
                    translationRadioButtonGroupSelection = inputs.itemById('translationRadioButtonGroup').selectedItem.name
                    if (translationRadioButtonGroupSelection == "constant distance for all bodies"):
                        apply_translation_transform = translation_transform
                    elif (translationRadioButtonGroupSelection == "compound distance for each copy"):
                        apply_translation_transform = compound_transform(translation_transform, k+1)
                    elif (translationRadioButtonGroupSelection == "compound distance and scale for each copy"):
                        apply_translation_transform = compound_translation_scaling(translation_transform, scale_transform, k+1)

                    translation_randomization_x = inputs.itemById('translation_randomization_x').valueOne
                    translation_randomization_y = inputs.itemById('translation_randomization_y').valueOne
                    translation_randomization_z = inputs.itemById('translation_randomization_z').valueOne
                    x_translation = translation_transform.getCell(0,3)
                    y_translation = translation_transform.getCell(1,3)
                    z_translation = translation_transform.getCell(2,3)
                    total_x_translation = apply_translation_transform.getCell(0,3)
                    total_y_translation = apply_translation_transform.getCell(1,3)
                    total_z_translation = apply_translation_transform.getCell(2,3)
                    total_x_translation = total_x_translation + x_translation * translation_randomization_x * random.uniform(-1,1) / 100
                    total_y_translation = total_y_translation + y_translation * translation_randomization_y * random.uniform(-1,1) / 100
                    total_z_translation = total_z_translation + z_translation * translation_randomization_z * random.uniform(-1,1) / 100
                    apply_translation_transform.setCell(0, 3, total_x_translation)
                    apply_translation_transform.setCell(1, 3, total_y_translation)
                    apply_translation_transform.setCell(2, 3, total_z_translation)
    
                    app.log('    with transformation array: ' + str(apply_translation_transform.asArray()))
                    if (apply_translation_transform.isEqualTo(adsk.core.Matrix3D.create())):
                        app.log('    which is identity matrix, so not performing matrix transformation')
                    else:
                        if (do_apply_transformations_recursively == True):
                            app.log('    !!!!!!! applying transformations recursively for translation')
                            translateFeatureInput = moveFeats.createInput(cumulativeBodiesCollection, apply_translation_transform)
                        else:
                            translateFeatureInput = moveFeats.createInput(bodiesCollection[k+1], apply_translation_transform)
                        moveFeats.add(translateFeatureInput)

                if (do_external_rotation_flag == True):
                    app.log('  EXTERNALLY ROTATING: ' + ' copy ' + str(k+1) + ' body: ' + str(selected_body_index))
                    externalRotationRadioButtonGroupSelection = inputs.itemById('externalRotationRadioButtonGroup').selectedItem.name
                    if (externalRotationRadioButtonGroupSelection == "constant angle for all bodies"):
                        apply_external_rotation_transform = external_rotation_transform
                    elif (externalRotationRadioButtonGroupSelection == "compound angle for each copy"):
                        apply_external_rotation_transform = compound_transform(external_rotation_transform, k+1)

                    external_rotation_randomization = inputs.itemById('external_rotation_randomization').valueOne
                    if (external_rotation_randomization > 0):
                        random_external_rotation_transform = adsk.core.Matrix3D.create()
                        random_external_rotation_transform.setToRotation((math.pi / 180.0) * random.uniform(0,external_rotation_randomization), get_random_vector(), centerPoint)
                        apply_external_rotation_transform.transformBy(random_external_rotation_transform)


                    app.log('    with transformation array: ' + str(apply_external_rotation_transform.asArray()))
                    if (apply_external_rotation_transform.isEqualTo(adsk.core.Matrix3D.create())):
                        app.log('    which is identity matrix, so not performing matrix transformation')
                    else:
                        if (do_apply_transformations_recursively == True):
                            app.log('    !!!!!!! applying transformations recursively for external rotation')
                            external_rotateFeatureInput = moveFeats.createInput(cumulativeBodiesCollection, apply_external_rotation_transform)
                        else:
                            external_rotateFeatureInput = moveFeats.createInput(bodiesCollection[k+1], apply_external_rotation_transform)
                        moveFeats.add(external_rotateFeatureInput)        

            # REMOVE ORIGINAL BODIES
            if (do_remove_original_bodies):
                for selected_body_index in range(originalBodiesCollection.count):
                    # delete the selected body.
                    body = originalBodiesCollection.item(selected_body_index)
                    app.log('  REMOVING ORIGINAL BODY: ' + body.name)
                    #body.deleteMe()
                    removeFeat = removeFeats.add(body)

            ## INTERFERENCE CHECK        
            if (preview_interference_flag):
                app.log('  CHECKING INTERFERENCES BETWEEN BODIES')

                allBodiesCollection = adsk.core.ObjectCollection.create()

                if (not do_remove_original_bodies):
                    for body in originalBodiesCollection:
                        allBodiesCollection.add(body)
                for k in range(num_copies+1):
                    for body in bodiesCollection[k]:
                        app.log('   adding entity to allBodiesCollection with name:' + str(body.name))                       
                        allBodiesCollection.add(body)
                
                app.log('   for ' + str(allBodiesCollection.count) + ' bodies')

                # Set the design type to DirectDesignType (for non-parametric modelling)        
                design.designType = adsk.fusion.DesignTypes.DirectDesignType

                # Create the interferenceInput object and run the analysis.
                interferenceInput = design.createInterferenceInput(allBodiesCollection)
                interferenceInput.areCoincidentFacesIncluded = False
                results = design.analyzeInterference(interferenceInput)    
                app.log('   interference results size: ' + str(results.count))

                if (results.count == 0):
                    ui.messageBox('There is NO interference between any of the ' + str(allBodiesCollection.count) + ' bodies')
                else:
                    # Create bodies for every intersection.  This is not supported in Parametric designs.
                    interferenceBodies = results.createBodies(True)
                    
                    # Activate the Intersections component created by Fusion that stores the interference bodies
                    occurrences = rootComp.occurrences
                    app.log('   number of occurrences: ' + str(occurrences.count))

#                    if (occurrences.count == 0):
#                        occurrences = new 

                    resultsOccurrence = occurrences.item(occurrences.count-1)
                    resultsOccurrence.activate()
                    
                    # Fit the view        
                    viewport = app.activeViewport
                    viewport.fit()
                    
                    # Report the results
                    bod = 0        
                    for res in results:
                        comp1Name = res.entityOne.parentComponent.name
                        comp2Name = res.entityTwo.parentComponent.name
                        bodyVolume = str(round(res.interferenceBody.volume, 2))
                        interferenceBodies.item(bod).name = 'Interference between ' + comp1Name + ' & ' + comp2Name
                        ui.messageBox('There is interference between ' + comp1Name + ' and ' + comp2Name + ' with a volume of ' + bodyVolume + ' cubic centimeters')
                        bod += 1

                # Set that the preview results can be used as the execute result.
                design.designType = adsk.fusion.DesignTypes.ParametricDesignType

            # CREATE COMPONENT FOR NEW BODY
            if (do_create_new_component_for_each_body == True):
                for k in range(num_copies+1):
                    for new_body in bodiesCollection[k]:
                        new_component_body = new_body.createComponent()
                        new_component_body.parentComponent.name = new_body.name
                        
            args.isValidResult = True
    preview_interference_flag = False

def get_random_vector():
    x = random.uniform(-1.0, 1.0) 
    y = random.uniform(-1.0, 1.0) 
    z = random.uniform(-1.0, 1.0) 
    if ((x**2 + y**2 + z**2) > 1):
        return get_random_vector()
    else:
        return adsk.core.Vector3D.create(x, y, z)

# This function will call a transform on itself multiple times
def compound_transform(transform: adsk.core.Matrix3D, number_of_times:int):
    output_transform = adsk.core.Matrix3D.create()
    for i in range(number_of_times):
        output_transform.transformBy(transform)
    return output_transform

# This function will calculate the overall translation matrix based on compounding multiple scaled translations
def compound_translation_scaling(transform_translation: adsk.core.Matrix3D, transform_scaling: adsk.core.Matrix3D, number_of_times:int):
    #app.log ("   compound translation scaling " + str(number_of_times) + " with translation matrix " + str(transform_translation.asArray()) + " and scaling matrix " + str(transform_scaling.asArray()))
    output_transform = adsk.core.Matrix3D.create()
    x_translation = transform_translation.getCell(0,3)
    y_translation = transform_translation.getCell(1,3)
    z_translation = transform_translation.getCell(2,3)
    x_scaling = transform_scaling.getCell(0,0)
    y_scaling = transform_scaling.getCell(1,1)
    z_scaling = transform_scaling.getCell(2,2)
    if (x_scaling == 1):
        output_x_translation = x_translation * number_of_times
    else:
        output_x_translation = x_translation * (x_scaling**(number_of_times) - 1)/ (x_scaling -1)
    if (y_scaling == 1):
        output_y_translation = y_translation * number_of_times
    else:
        output_y_translation = y_translation * (y_scaling**(number_of_times) - 1)/ (y_scaling -1)
    if (z_scaling == 1):
        output_z_translation = z_translation * number_of_times
    else:
        output_z_translation = z_translation * (z_scaling**(number_of_times) - 1)/ (z_scaling -1)
    output_transform.setCell(0, 3, output_x_translation)
    output_transform.setCell(1, 3, output_y_translation)
    output_transform.setCell(2, 3, output_z_translation)
    return output_transform

# This function will be called when the user changes anything in the command dialog
def command_input_changed(args: adsk.core.InputChangedEventArgs):
#    global update_preview_flag
    global preview_interference_flag
    global scale_transform
    global internal_rotation_transform
    global translation_transform
    global external_rotation_transform
    global activeTab
    global oldTab

#    update_preview_flag = True
    changed_input = args.input
    inputs = args.inputs
#    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id} and {changed_input.name} to value {changed_input}')
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to id {changed_input.id} and name {changed_input.name}')
    if (changed_input.id == 'reset scale'):
        futil.log(f'   transform value as array: {scale_transform.asArray()}')
        inputs.itemById('scale_value').text = str('1.0')
        inputs.itemById('scale_value_x').text = str('1.0')
        inputs.itemById('scale_value_y').text = str('1.0')
        inputs.itemById('scale_value_z').text = str('1.0')
        inputs.itemById('scale_randomization').valueOne = 0
        inputs.itemById('scale_randomization_x').valueOne = 0
        inputs.itemById('scale_randomization_y').valueOne = 0
        inputs.itemById('scale_randomization_z').valueOne = 0

    if (changed_input.id == 'reset internal rotation'):
        inputs.itemById('internal_rotation_triad').transform = adsk.core.Matrix3D.create()
        inputs.itemById('internal_rotation_randomization').valueOne = 0
        internal_rotation_transform = inputs.itemById('internal_rotation_triad').transform
        futil.log(f'   transform value as array: {internal_rotation_transform.asArray()}')

    if (changed_input.id == 'reset translation'):
        inputs.itemById('translation_triad').transform = adsk.core.Matrix3D.create()
        inputs.itemById('translation_randomization_x').valueOne = 0
        inputs.itemById('translation_randomization_y').valueOne = 0
        inputs.itemById('translation_randomization_z').valueOne = 0
        translation_transform = inputs.itemById('translation_triad').transform
        futil.log(f'   transform value as array: {translation_transform.asArray()}')

    if (changed_input.id == 'reset external rotation'):
        inputs.itemById('external_rotation_triad').transform = adsk.core.Matrix3D.create()
        inputs.itemById('external_rotation_randomization').valueOne = 0
        external_rotation_transform = inputs.itemById('external_rotation_triad').transform
        futil.log(f'   transform value as array: {external_rotation_transform.asArray()}')

    if (changed_input.id == 'preview interference'):
        preview_interference_flag = True

    if (changed_input.id == 'scaleEquationRadioButtonGroup'):
        scale_equation_radio_button: adsk.core.RadioButtonGroupCommandInput = inputs.itemById('scaleEquationRadioButtonGroup')
        if (scale_equation_radio_button.selectedItem.name == 'scale uniformly'):
            scaleValueInput = inputs.itemById('scale_value')
            scaleValueInput.isEnabled = True
            scaleValueInput.isVisible = True
            scaleValueInputX = inputs.itemById('scale_value_x')
            scaleValueInputX.isEnabled = False
            scaleValueInputX.isVisible = False    
            scaleValueInputY = inputs.itemById('scale_value_y')
            scaleValueInputY.isEnabled = False
            scaleValueInputY.isVisible = False
            scaleValueInputZ = inputs.itemById('scale_value_z')
            scaleValueInputZ.isEnabled = False
            scaleValueInputZ.isVisible = False
            scaleRandomization = inputs.itemById('scale_randomization')
            scaleRandomization.isEnabled = True
            scaleRandomization.isVisible = True
            scaleRandomizationX = inputs.itemById('scale_randomization_x')
            scaleRandomizationX.isEnabled = False
            scaleRandomizationX.isVisible = False
            scaleRandomizationY = inputs.itemById('scale_randomization_y')
            scaleRandomizationY.isEnabled = False
            scaleRandomizationY.isVisible = False
            scaleRandomizationZ = inputs.itemById('scale_randomization_z')
            scaleRandomizationZ.isEnabled = False
            scaleRandomizationZ.isVisible = False
        else:
            scaleValueInput = inputs.itemById('scale_value')
            scaleValueInput.isEnabled = False
            scaleValueInput.isVisible = False
            scaleValueInputX = inputs.itemById('scale_value_x')
            scaleValueInputX.isEnabled = True
            scaleValueInputX.isVisible = True
            scaleValueInputY = inputs.itemById('scale_value_y')
            scaleValueInputY.isEnabled = True
            scaleValueInputY.isVisible = True
            scaleValueInputZ = inputs.itemById('scale_value_z')
            scaleValueInputZ.isEnabled = True
            scaleValueInputZ.isVisible = True
            scaleRandomization = inputs.itemById('scale_randomization')
            scaleRandomization.isEnabled = False
            scaleRandomization.isVisible = False
            scaleRandomizationX = inputs.itemById('scale_randomization_x')
            scaleRandomizationX.isEnabled = True
            scaleRandomizationX.isVisible = True
            scaleRandomizationY = inputs.itemById('scale_randomization_y')
            scaleRandomizationY.isEnabled = True
            scaleRandomizationY.isVisible = True
            scaleRandomizationZ = inputs.itemById('scale_randomization_z')
            scaleRandomizationZ.isEnabled = True
            scaleRandomizationZ.isVisible = True
    if (changed_input.id == 'APITabBar'):
#        update_preview_flag = False
        oldTab = 'none'
        if (tabCmdInputCopy.isActive):
            futil.log(f'  Copy Tab is active')
            oldTab = activeTab
            activeTab = 'tab_copy'            
        else:
            futil.log(f'  Copy Tab is inactive')

        if (tabCmdInputScale.isActive):
            futil.log(f'  Scale Tab is active')
            oldTab = activeTab
            activeTab = 'tab_scale'            
        else:
            futil.log(f'  Scale Tab is inactive')

        if (tabCmdInputInternalRotation.isActive):
            futil.log(f'  Internal Rotation Tab is active')
            oldTab = activeTab
            activeTab = 'tab_internal_rotation'            
            inputs.itemById('internal_rotation_triad').setRotateVisibility(True)
            inputs.itemById('internal_rotation_triad').transform = internal_rotation_transform
        else:
            futil.log(f'  Internal Rotation Tab is inactive')

        if (tabCmdInputTranslation.isActive):
            futil.log(f'  Translation Tab is active')
            oldTab = activeTab
            activeTab = 'tab_translation'            
            inputs.itemById('translation_triad').setTranslateVisibility(True)
            inputs.itemById('translation_triad').transform = translation_transform
        else:
            futil.log(f'  Translation Tab is inactive')
            
        if (tabCmdInputExternalRotation.isActive):
            futil.log(f'  External Rotation Tab is active')
            oldTab = activeTab
            activeTab = 'tab_external_rotation'            
            inputs.itemById('external_rotation_triad').setRotateVisibility(True)
            inputs.itemById('external_rotation_triad').transform = external_rotation_transform
        else:
            futil.log(f'  External Rotation Tab is inactive')

        if (tabCmdInputPreview.isActive):
            futil.log(f'  Preview Tab is active')
            oldTab = activeTab
            activeTab = 'tab_preview'            
        else:
            futil.log(f'  Preview Tab is inactive')

        if (oldTab == 'tab_internal_rotation'):
            internal_rotation_transform = inputs.itemById('internal_rotation_triad').transform
            inputs.itemById('internal_rotation_triad').hideAll()
        elif (oldTab == 'tab_translation'):
            translation_transform = inputs.itemById('translation_triad').transform
            inputs.itemById('translation_triad').hideAll()
        elif (oldTab == 'tab_external_rotation'):
            external_rotation_transform = inputs.itemById('external_rotation_triad').transform
            inputs.itemById('external_rotation_triad').hideAll()



    if (changed_input.id == 'internal_rotation_triad'):
        futil.log(f'   transform value as array: {changed_input.transform.asArray()}')
        internal_rotation_transform = inputs.itemById('internal_rotation_triad').transform
    if (changed_input.id == 'translation_triad'):
        futil.log(f'   transform value as array: {changed_input.transform.asArray()}')
        translation_transform = inputs.itemById('translation_triad').transform
    if (changed_input.id == 'external_rotation_triad'):
        futil.log(f'   transform value as array: {changed_input.transform.asArray()}')
        external_rotation_transform = inputs.itemById('external_rotation_triad').transform
  



# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    global local_handlers
    local_handlers = []
    futil.log(f'{CMD_NAME} Command Destroy Event')
