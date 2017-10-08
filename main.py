import bpy
import re
import bpy_extras
import bmesh

# やはり人の作ったものは美しい
# 完璧なアドオンだ

bl_info = {
    "name": "Viewport Rename",
    "author": "poor",
    "version": (0, 2),
    "blender": (2, 77, 0),
    "location": "3D View > Ctrl+R",
    "category": "3D View"
}

def move_from_camera(length):
    #モードチェック
    if(bpy.context.object.mode == 'EDIT'):
        # もし選択されているのが頂点なら
        # その頂点のワールド座標を求める
        # 移動後のワールド座標を求める
        # ワールド座標をローカル座標に変換する
        # ローカル座標を変換する
        print("aaa");
        mesh = bpy.context.object.data
        selected_verts = list(filter(lambda v: v.select, mesh.vertices))

        # for v in mesh.vertices:
        #     print(v.co)

        # bpy.ops.object.mode_set(mode='OBJECT')
        # bm.from_mesh(bpy.context.object.data)
        bm = bmesh.from_edit_mesh(bpy.context.object.data)
        mat_world = bpy.context.object.matrix_world
        mat_inverted = mat_world.inverted()
        camera_location = bpy.context.scene.camera.location

        for i in bm.verts:
            if i.select == True:
                vert = i
                object_location = mat_world * vert.co
                move_vector = object_location - camera_location
                move_vector = move_vector.normalized()
                vert.co = object_location + move_vector * length
                vert.co = mat_inverted * vert.co
                # bpy.ops.transform.translate(value=move_vector * length, constraint_axis=(False, False, False),
                #                             constraint_orientation='GLOBAL', mirror=False, proportional='DISABLED',
                #                             proportional_edit_falloff='SMOOTH', proportional_size=1)
                # vert.co = mat_world.inverted() * (bpy.context.active_object.location + move_vector * length)
        bmesh.update_edit_mesh(mesh)
        # bm.to_mesh(mesh)
        # bm.free()
        # bpy.ops.object.mode_set(mode='EDIT')

    elif(bpy.context.object.mode == 'OBJECT'):
        print("aaaxxxxxxxx");
        object_location = bpy.context.object.location
        camera_location = bpy.context.scene.camera.location
        move_vector = object_location - camera_location
        move_vector = move_vector.normalized()
        bpy.context.active_object.location = bpy.context.active_object.location + move_vector * length

def get_screen_position(co):
    scene = bpy.context.scene

    obj = bpy.context.scene.camera
    # obj = bpy.context.object

    co = co.location
    # co = bpy.context.active_object.location
    # co = bpy.context.scene.cursor_location

    co_2d = bpy_extras.object_utils.world_to_camera_view(scene, obj, co)
    print("2D Coords:", co_2d)

    # If you want pixel coords
    render_scale = scene.render.resolution_percentage / 100
    render_size = (
        int(scene.render.resolution_x * render_scale),
        int(scene.render.resolution_y * render_scale),
    )
    print("Pixel Coords:", (
        round(co_2d.x * render_size[0]),
        round(co_2d.y * render_size[1]),
    ))
    return (co_2d.x * render_size[0],co_2d.y * render_size[1],0)

class ModalOperator(bpy.types.Operator):
    bl_idname = "object.modal_operator"
    bl_label = "Simple Modal Operator"
    type2 = bpy.props.FloatProperty(name="Test Prob", default=0, step=1)

    # Init
    def __init__(self):
        print("init")

    # invoke
    def invoke(self, context, event):
        print("invoke");
        # self.init_loc_x = context.object.location.x
        # self.init_loc_x = context.object.location.y
        self.mouse_initial_x = event.mouse_x
        self.mouse_initial_y = event.mouse_y
        self.value = 0
        self.temp = event.mouse_y
        #self.value = event.mouse_xa
        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    # Actual content
    def execute(self, context):
        print("excute");
        move_from_camera(self.value / 100.0)
        # context.object.location.x = self.init_loc_x + self.value / 100.0
        return {'FINISHED'}

    # While loop
    def modal(self, context, event):
        print("modal");
        if event.type == 'MOUSEMOVE':  # Apply
            # Use UP / DOWN
            self.value = self.temp - event.mouse_y
            self.temp = event.mouse_y

            print(self.value)
            self.execute(context)
        elif event.type == 'LEFTMOUSE':  # Confirm
            return {'FINISHED'}
        elif event.type in {'RIGHTMOUSE', 'ESC'}:  # Cancel
            move_from_camera(0)
            #context.object.location.x = self.init_loc_x
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    # End
    def __del__(self):
        print("del")



#bpy.utils.register_class(ModalOperator)
# test call
#bpy.ops.object.modal_operator('INVOKE_DEFAULT')


class ViewportRenameOperator(bpy.types.Operator):
    """Rename Objects in 3d View"""
    bl_idname = "view3d.perspective_magic"
    bl_label = "Perspective Magic"
    bl_options = {'REGISTER', 'UNDO'}
    type = bpy.props.StringProperty()
    type2 = bpy.props.FloatProperty(name="Test Prob",default=0,step=1)

    @classmethod
    def poll(cls, context):
        # return (bool(context.selected_objects))
        return True

    def execute(self, context):
        # get_screen_position(bpy.context.active_object)
        move_from_camera(self.type2)

        return {'FINISHED'}

        if False:
            scn = context.scene
            self.report({'INFO'}, "Hello World")

            user_input = self.type
            reverse = False
            if user_input.endswith("#r"):
                reverse = True
                user_input = user_input[:-1]

            suff = re.findall("#+$", user_input)
            if user_input and suff:
                number = ('%0'+str(len(suff[0]))+'d', len(suff[0]))
                real_name = re.sub("#", '', user_input)

                objs = context.selected_objects[::-1] if reverse else context.selected_objects
                names_before = [n.name for n in objs]
                for c, o in enumerate(objs, start=1):
                    o.name = (real_name + (number[0] % c))
                self.report({'INFO'}, "Renamed {}".format(", ".join(names_before)))
                return {'FINISHED'}

            elif user_input:
                #Correct Input
                old_name = context.active_object.name
                context.active_object.name = user_input
                self.report({'INFO'}, "{} renamed to {}".format(old_name, user_input))
                return {'FINISHED'}

            else:
                #No input
                self.report({'INFO'}, "No input, operation cancelled")
                return {'CANCELLED'}

    def disable_invoke(self, context, event):
        wm = context.window_manager
        self.type = context.active_object.name
        #return wm.invoke_popup(self, width=400, height=200)
        return wm.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout
        # row.prop(self, "type", text="New name")
        row.prop(self, "type2", text="New name")


# ------------------------------------------------------------------------
#    register and unregister functions
# ------------------------------------------------------------------------

addon_keymaps = []

def register():
    # bpy.utils.register_module(__name__)
    bpy.utils.register_class(ViewportRenameOperator)
    bpy.utils.register_class(ModalOperator)

    # handle the keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(ModalOperator.bl_idname, type='J', value='PRESS', ctrl=True)
        addon_keymaps.append((km, kmi))

def unregister():

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # bpy.utils.unregister_module(__name__)
    bpy.utils.unregister_class(ViewportRenameOperator)
    bpy.utils.unregister_class(ModalOperator)
    #del bpy.types.Scene.viewport_rename

if __name__ == "__main__":
    register()

try:
    unregister()
except:
    pass
finally:
    register()