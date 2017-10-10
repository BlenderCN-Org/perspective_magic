import bpy
import re
import bpy_extras
import bmesh
import mathutils

# やはり人の作ったものは美しい
# 完璧なアドオンだ

bl_info = {
    "name": "Perspective Magic",
    "author": "poor",
    "version": (0, 1),
    "blender": (2, 79, 0),
    "location": "3D View > Ctrl+J",
    "category": "3D View"
}

def move_from_camera(length):
    # ペアレントがある場合にうまくいかない可能性がある。検証する
    # カメラは常に設定されていなければならない
    # メッシュエディットモードでなければならない

    camera_location = bpy.context.scene.camera.location

    #モードチェック
    if(bpy.context.object.mode == 'EDIT'):
        # もし選択されているのが頂点なら
        # その頂点のワールド座標を求める
        # 移動後のワールド座標を求める
        # ワールド座標をローカル座標に変換する
        # ローカル座標を変換する
        mesh = bpy.context.object.data
        selected_verts = list(filter(lambda v: v.select, mesh.vertices))

        # for v in mesh.vertices:
        #     print(v.co)

        # bpy.ops.object.mode_set(mode='OBJECT')
        # bm.from_mesh(bpy.context.object.data)
        bm = bmesh.from_edit_mesh(bpy.context.object.data)
        mat_world = bpy.context.object.matrix_world
        mat_inverted = mat_world.inverted()


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
        object_location = bpy.context.object.location
        move_vector = object_location - camera_location
        move_vector = move_vector.normalized()
        bpy.context.active_object.location = bpy.context.active_object.location + move_vector * length

def get_screen_position(co):
    scene = bpy.context.scene

    obj = bpy.context.scene.camera
    # obj = bpy.context.object

    # co = bpy.context.active_object.location
    # co = bpy.context.scene.cursor_location

    co_2d = bpy_extras.object_utils.world_to_camera_view(scene, obj, co)
    # print("2D Coords:", co_2d)

    # If you want pixel coords
    render_scale = scene.render.resolution_percentage / 100
    render_size = (
        int(scene.render.resolution_x * render_scale),
        int(scene.render.resolution_y * render_scale),
    )
    # print("Pixel Coords:", (
    #    round(co_2d.x * render_size[0]),
    #    round(co_2d.y * render_size[1]),
    #))
    return mathutils.Vector((co_2d.x * render_size[0],co_2d.y * render_size[1],0))

class PerspectiveMagicModal(bpy.types.Operator):
    bl_idname = "object.perspective_magic_modal_operator"
    bl_label = "Perspective Magic Modal Operator"
    #type2 = bpy.props.FloatProperty(name="Test Prob", default=0, step=1)

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
        self.button = ""
        #self.value = event.mouse_xa
        self.execute(context)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    # Actual content
    def execute(self, context):
        print("excute");

        if self.button == "Shift":
            move_from_camera(self.value / 1000.0)
        elif self.button == "Ctrl":
            move_from_camera(self.value / 10.0)
        else:
            move_from_camera(self.value / 100.0)

        self.button = ""

        # context.object.location.x = self.init_loc_x + self.value / 100.0
        return {'FINISHED'}

    # While loop
    def modal(self, context, event):
        print("modal");
        if event.type == 'MOUSEMOVE':  # Apply
            # Use UP / DOWN
            self.value = self.temp - event.mouse_y
            self.temp = event.mouse_y

            if event.shift:
                self.button = "Shift"
            if event.ctrl:
                self.button = "Ctrl"

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

class PerspectiveMagic(bpy.types.Operator):
    """Rename Objects in 3d View"""
    bl_idname = "view3d.perspective_magic"
    bl_label = "Perspective Magic"
    bl_options = {'REGISTER', 'UNDO'}
    float_property = bpy.props.FloatProperty(name="Distance",default=0,step=1)

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        move_from_camera(self.type2)

        return {'FINISHED'}

    def draw(self, context):
        row = self.layout
        row.prop(self, "float_property", text="Distance")

# ------------------------------------------------------------------------
#    register and unregister functions
# ------------------------------------------------------------------------

addon_keymaps = []

def register():
    # bpy.utils.register_module(__name__)
    # bpy.utils.register_class(PerspectiveMagic)
    bpy.utils.register_class(PerspectiveMagicModal)

    # handle the keymap
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(PerspectiveMagicModal.bl_idname, type='J', value='PRESS', ctrl=True)
        addon_keymaps.append((km, kmi))

def unregister():

    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    # bpy.utils.unregister_module(__name__)
    # bpy.utils.unregister_class(PerspectiveMagic)
    bpy.utils.unregister_class(PerspectiveMagicModal)
    #del bpy.types.Scene.viewport_rename

if __name__ == "__main__":
    register()

# ----------------------------------------------------------------------------
# Test Here
# ----------------------------------------------------------------------------

class Struct:
    def __init__(self, A, AD, B, BD, center, length, mirror,al,adl):
        self.A = A
        self.AD = AD
        self.B = B
        self.BD = BD
        self.center = center
        self.length = length
        self.mirror = mirror
        self.al = al
        self.adl = adl

    def __repr__(self):
        return repr((self.length))

def change_empty_location(lens_size,sensor_size,t_array):

    bpy.context.scene.camera.data.lens = lens_size
    bpy.context.scene.camera.data.sensor_width = sensor_size

    width = 2

    rx = bpy.context.scene.render.resolution_x
    ry = bpy.context.scene.render.resolution_y

    height = 2 * ry / rx
    c_distance = 2 * lens_size/sensor_size

    t_array = []
    A = bpy.data.objects["A"].location;t_array.append(A)
    AD = bpy.data.objects["A'"].location;t_array.append(AD)
    B = bpy.data.objects["B"].location;t_array.append(B)
    BD = bpy.data.objects["B'"].location;t_array.append(BD)

    for unit in t_array:
        move = mathutils.Vector((0,c_distance,0))
        cl = bpy.context.scene.camera.location
        unit.y = (cl + move).y



print("TEST")


# lens_length = 1
# lens_limit = 16
# lens_step = 1
# min = 1
# limit = 16
# step = 0.1

lens_length = 4
lens_limit = 5
lens_step = 1

sensor_size = 1

min = 1
limit = 16
step = 0.1

while lens_length < lens_limit:
    camera_location = bpy.context.scene.camera.location



    A = bpy.data.objects["A"].location
    AD = bpy.data.objects["A'"].location
    B = bpy.data.objects["B"].location
    BD = bpy.data.objects["B'"].location

    t_array = [A,B,AD,BD]

    # 値を変えている部分 -----------------------------------------
    change_empty_location(lens_length,sensor_size,t_array)
    # ------------------------------------------------------------


    AE = (A - camera_location).normalized()
    ADE = (AD - camera_location).normalized()
    BE = (B - camera_location).normalized()

    BDScreen = get_screen_position(BD)



    a_length = min
    ad_length = min
    b_length = min


    array = []

    while a_length < limit:
        AM = camera_location + AE * a_length
        # bpy.ops.object.empty_add(type='PLAIN_AXES', view_align=False, location=AM, layers=(
        #    False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False,
        #    False, False, False, False))

        ad_length = min
        while ad_length < limit:
            ADM = camera_location + ADE * ad_length
            # bpy.ops.object.empty_add(type='PLAIN_AXES', view_align=False, location=ADM, layers=(
            #    False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False,
            #    False, False, False, False))

            center = (AM + ADM) / 2
            mirror = AM - center

            b_length = min
            while b_length < limit:
                BM = camera_location + BE * b_length

                BMirror = BM.reflect(mirror)

                BMirrorScreen = get_screen_position(BMirror)

                distance = BMirrorScreen - BDScreen

                temp = Struct(AM, ADM, BM, BMirror, center, distance.length, mirror,ad_length,a_length)
                array.append(temp)

                # print(distance.length)

                b_length += step
            # print(center)
            # bpy.ops.object.empty_add(type='PLAIN_AXES', view_align=False, location=center, layers=(
            #   False, True, False, False, False, False, False, False, False, False, False, False, False, False, False, False,
            #   False, False, False, False))


            ad_length += step
        a_length += step

    # Sort
    array = sorted(array, key=lambda struct: struct.length)
    # Display
    print(array[0].length,lens_length,array[0].al - 1,array[0].adl - 1)

    # 実際に変更を加えている部分 ----------------------------------------------------------------------------
    # Apply location and rotation to the Center
    bpy.data.objects["center"].location = array[0].center
    bpy.data.objects["center"].rotation_mode = 'QUATERNION'
    bpy.data.objects["center"].rotation_quaternion = array[0].mirror.to_track_quat('Z', 'Y')
    # -------------------------------------------------------------------------------------------------------

    lens_length += lens_step

# Debug ---------------------------------------------------------------------
debug = 0
if debug == 1:
    try:
        unregister()
    except:
        pass
    finally:
        register()
# ---------------------------------------------------------------------------
