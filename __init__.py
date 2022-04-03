#script to move rigify DEF bones into simple hierarchy
#HOWTO: right after generating rig using rigify
#	press armature -> Rigify move DEF bones  -> (Move DEF bones) button
bl_info = {
    "name": "Rigify move DEF bones",
    "category": "Rigging",
    "description": "Moves all DEF bones into simple hierarchy",
    "location": "At the bottom of Rigify rig data/armature tab",
    "blender":(2,80,0)
}

import bpy
import re


class RigTools_Panel(bpy.types.Panel):
    bl_label = "Rigify move DEF bones"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(self, context):
        return context.object.type == 'ARMATURE' and "DEF-spine" in bpy.context.object.data.bones
    
    def draw(self, context):
        self.layout.operator("rig_tools.move_def")
        
        
class RigTools_MoveDef(bpy.types.Operator):
    bl_idname = "rig_tools.move_def"
    bl_label = "Move DEF bones"

    def execute(self, context):
        ob = bpy.context.object

        remap = self.get_org_remap()
        remap.update(self.get_parent_remap())
        remap.update(self.get_special_remap())

        remove_bones_in_chain = [
            'DEF-upper_arm.L.001',
            'DEF-forearm.L.001',
            'DEF-upper_arm.R.001',
            'DEF-forearm.R.001',
            'DEF-thigh.L.001',
            'DEF-shin.L.001',
            'DEF-thigh.R.001',
            'DEF-shin.R.001'
        ]

        transform_copies = self.get_transform_copies()

        # add missing constraints
        bpy.ops.object.mode_set(mode='POSE')
        for bone_name in transform_copies:
            bone = ob.pose.bones[bone_name]
            constraint = bone.constraints.new('COPY_TRANSFORMS')
            constraint.target = ob
            constraint.subtarget = bone.parent.name

        # apply new parents
        bpy.ops.object.mode_set(mode='EDIT')

        for remap_key in remap:
            ob.data.edit_bones[remap_key].parent = ob.data.edit_bones[remap[remap_key]]

        # remove extra bones in chains
        bpy.ops.object.mode_set(mode='OBJECT')

        for bone_name in remove_bones_in_chain:
            if bone_name in ob.data.bones:
                ob.data.bones[bone_name].use_deform = False

        bpy.ops.object.mode_set(mode='EDIT')

        for bone_name in remove_bones_in_chain:
            if bone_name in ob.data.bones:
                remove_bone = ob.data.edit_bones[bone_name]
                parent_bone = remove_bone.parent
                parent_bone.tail = remove_bone.tail
                retarget_bones = list(remove_bone.children)
                for bone in retarget_bones:
                    bone.parent = parent_bone
                ob.data.edit_bones.remove(remove_bone)

        # rename some bones
        bpy.ops.object.mode_set(mode='OBJECT')

        namelist = [
            ("DEF-spine.006", "DEF-head"),
            ("DEF-spine.005", "DEF-neck")
        ]

        for name, newname in namelist:
            # get the pose bone with name
            pb = ob.pose.bones.get(name)
            # continue if no bone of that name
            if pb is None:
                continue
            # rename
            pb.name = newname

        self.report({'INFO'}, 'Unity ready rig!')                

        return{'FINISHED'}

    def get_parent_remap(self):
        remap = {}
        ob = bpy.context.object

        bpy.ops.object.mode_set(mode='OBJECT')

        for bone in ob.data.bones:
            if self.is_def_bone(bone.name):
                srch_bone = bone.parent
                while srch_bone != None:
                    if self.is_def_bone(srch_bone.name):
                        remap[bone.name] = srch_bone.name
                        break
                    srch_bone = srch_bone.parent

        return remap

    def get_transform_copies(self):
        result = []
        ob = bpy.context.object

        bpy.ops.object.mode_set(mode='POSE')
        for bone in ob.pose.bones:
            if self.is_def_bone(bone.name) and not self.has_transform_copies(bone):
                result.append(bone.name)
        return result

    def has_transform_copies(self, bone):
        for constraint in bone.constraints:
            if constraint.type == 'COPY_TRANSFORMS':
                return True
        return False

    def is_def_bone(self, bone_name):
        return bone_name[0:4] == 'DEF-'

    def is_org_bone(self, bone_name):
        return bone_name[0:4] == 'ORG-'

    def get_proto_name(self, bone_name):
        if self.is_def_bone(bone_name) or self.is_org_bone(bone_name):
            return bone_name[4:]
        else:
            return bone_name

    def get_missing_bones(self, remap):
        result = []
        ob = bpy.context.object
        for bone in ob.data.bones:
            if self.is_def_bone(bone.name) and not bone.name in remap:
                result.append(bone.name)
        return result

    def get_org_remap(self):
        remap = {}
        ob = bpy.context.object

        bpy.ops.object.mode_set(mode='OBJECT')

        for bone in ob.data.bones:
            if self.is_def_bone(bone.name):
                name = self.get_proto_name(bone.name)
                parent = bone.parent
                parent_name = self.get_proto_name(parent.name)
                if parent_name == name:
                    parent = parent.parent
                    parent_name = self.get_proto_name(parent.name)
                    if ('DEF-' + parent_name) in ob.data.bones:
                        remap[bone.name] = 'DEF-' + parent_name
        return remap

    def get_special_remap(self):
        return {
            'DEF-thigh.L': 'DEF-pelvis.L',
            'DEF-thigh.R': 'DEF-pelvis.R',
            'DEF-upper_arm.L': 'DEF-shoulder.L',
            'DEF-upper_arm.R': 'DEF-shoulder.R'
        }

def register():
    #classes     
    bpy.utils.register_class(RigTools_Panel)
    bpy.utils.register_class(RigTools_MoveDef)
    
    
def unregister():
    #classes
    bpy.utils.unregister_class(RigTools_Panel)
    bpy.utils.unregister_class(RigTools_MoveDef)
