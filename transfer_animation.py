bl_info = {
    
    'name': 'transfer_animation',
    'blender': (2, 82, 0),
    'category': 'Animation',
    'version': (1, 0, 0),
    'author': 'Emil Johansson',
    'description': 'Transfer animation to an identical skeleton'
}
import bpy
import mathutils as math
import math as m
from bpy.types import Operator, OperatorFileListElement
from bpy.props import CollectionProperty, StringProperty
from decimal import *

getcontext().prec = 6
#globals

scene = bpy.context.scene
sourceIndexMap = {} #must be identical in index for both source and target

sourceKeys = []
sourceKeyProps = []

sourceSkeletonName = ""
sourcePoseBoneList=[] 
sourceBoneNameList=[]

sourceParentList = []
sourceParentList2 = []

sourceRotationList = []
sourceOrientationList = [] #does not need to be a 2d array

sourceEditBoneMap = {}
sourceBindPoseBones = []

locations = []
scale = []

targetIndexMap = {} #must be identical in index for both source and target

targetPoseBoneList=[] 
targetBoneNameList=[]

targetParentList = []
targetParentList2 = []
targetRotationList = []
targetOrientationList = []

targetEditBoneMap={}

targetSkeletonName = ""
targetBindPoseBones = []

parentChainsList = []





def changeOrientation(skeleton):
    
    
    sourceSkeleton = bpy.data.objects[sourceSkeletonName]
    bpy.ops.object.mode_set(mode='POSE')
    ikList = []
    for index, pbone in enumerate(sourceSkeleton.pose.bones):
        if pbone.is_in_ik_chain:
            ikList.append(index)
    
    
    
    
    bpy.ops.object.mode_set(mode='EDIT')
    rollMap = {}
    axisMap = {}
    headMap = {}
    tailMap = {}
    for ebone in sourceSkeleton.data.edit_bones:
        rollMap[ebone.name] = ebone.roll
        axisMap[ebone.name] = ebone.vector
        headMap[ebone.name] = ebone.head
        tailMap[ebone.name] = ebone.tail
        
        
    
    chainLists= []
    for x in range(0, len(skeleton.data.edit_bones)):
        if len(skeleton.data.edit_bones[x].children)==0:
            list = chainParents(x)
            list.reverse()
            list.append(x)
            chainLists.append(list)
    taken = []
    for chain in chainLists:
        
        for index, bone in enumerate(chain):
            if bone in taken:
                continue
            condition1 = skeleton.data.edit_bones[bone].use_connect == False
            condition2 = index == 0
            condition3 = bone in ikList and skeleton.data.edit_bones[bone].parent in iiKlist == False
            if  condition1 or condition2 or condition3:
                print(sourceBoneNameList[bone])
                dir = skeleton.data.edit_bones[bone].vector + (axisMap[sourceBoneNameList[bone]] -skeleton.data.edit_bones[bone].vector)
                #dir = dir.normalized()
                #up = math.Vector((0,0,1))
                #xAxis = up.cross(dir)
                #xAxis = xAxis.normalized()
                #yAxis = dir.cross(xAxis)
                #yAxis = yAxis.normalized()
                    
                #rotM = math.Matrix().to_3x3()
                #rotM[0][0] = xAxis.x
                #rotM[1][0] = yAxis.x
                #rotM[2][0] = dir.x
                    
                #rotM[0][1] = xAxis.y
                #rotM[1][1] = yAxis.y
                #rotM[2][1] = dir.y
                    
                #rotM[0][2] = xAxis.z
                #rotM[1][2] = yAxis.z
                #rotM[2][2] = dir.z
                    
                #skeleton.data.edit_bones[bone].transform(rotM, scale = False, roll = False)
                skeleton.data.edit_bones[bone].tail = (dir + headMap[sourceBoneNameList[bone]])
                skeleton.data.edit_bones[bone].head = (skeleton.data.edit_bones[bone].tail - dir)
                skeleton.data.edit_bones[bone].roll = rollMap[sourceBoneNameList[bone]]
            else:
                #print(tailMap[sourceBoneNameList[bone]], sourceBoneNameList[bone] )    
                skeleton.data.edit_bones[bone].tail = tailMap[sourceBoneNameList[bone]]
                skeleton.data.edit_bones[bone].roll = rollMap[sourceBoneNameList[bone]]
                
            taken.append(bone)
            
    
    bpy.ops.object.mode_set(mode='POSE')


def calcRotMat(frameIndex, currentBoneIndex):
       
    #Isolate Bone
    sBindposeInversed = sourceBindPoseBones[currentBoneIndex].inverted()
    sRotation  = sourceRotationList[frameIndex][currentBoneIndex]
    
    isolatedRotation  =sBindposeInversed @ sRotation
     
    #Convert to World Space
    #sOrientation = sourceOrientationList[currentBoneIndex]
    #sParents = sourceParentList[currentBoneIndex]
    
    #worldSpaceRotation = sOrientation.inverted() @ sParents.inverted() @ isolatedRotation @ sParents @ sOrientation
    worldSpaceRotation = bpy.context.object.convert_space(pose_bone=sourcePoseBoneList[currentBoneIndex], 
            matrix=isolatedRotation.to_4x4(), 
            from_space='POSE', 
            to_space='WORLD').to_3x3()
    #Convert to target space
    
    #tOrientation = targetOrientationList[currentBoneIndex]
    #tParents = targetParentList[currentBoneIndex]
    
    #translatedRotation = tOrientation @ tParents @ worldSpaceRotation @ tParents.inverted() @ tOrientation.inverted()
    
    translatedRotation = bpy.context.object.convert_space(pose_bone=targetPoseBoneList[currentBoneIndex], 
            matrix=worldSpaceRotation.to_4x4(), 
            from_space='WORLD', 
            to_space='POSE').to_3x3()
        
    # final
    tBindpose  = targetBindPoseBones[currentBoneIndex]
    
    finalRotation = tBindpose @ translatedRotation
    
    return finalRotation

def calcParentMatrices(currentBoneIndex, source):
    
    parent = math.Matrix.Identity(3)
    if source:
        if sourcePoseBoneList[currentBoneIndex].parent != None:
            parentIndex = sourceIndexMap[sourcePoseBoneList[currentBoneIndex].parent.name]
            parent = parent @ sourceRotationList[0][parentIndex]
            parent = parent @ sourceOrientationList[parentIndex]
            parent = parent @ calcParentMatrices(parentIndex, source)
            
        
            
    else:
        if targetPoseBoneList[currentBoneIndex].parent != None:
            parentIndex = targetIndexMap[targetPoseBoneList[currentBoneIndex].parent.name]
            parent = parent @ targetRotationList[0][parentIndex]
            parent = parent @ targetOrientationList[parentIndex]
            parent = parent @ calcParentMatrices(parentIndex, source)
          
    
    return parent


def chainParents(currentBoneIndex):
    chain = []
    
    if sourcePoseBoneList[currentBoneIndex].parent != None:
        parentIndex = sourceIndexMap[sourcePoseBoneList[currentBoneIndex].parent.name]
        chain.append(parentIndex)
        for x in chainParents(parentIndex):
            chain.append(x)
    return chain

def getRotandOrient(bones,editbones, rotationList,orientationList, bindList, skeleton):
    
    axisMap = {}
    rollMap = {}
    rotationList.clear()
    orientationList.clear()
    bindList.clear()
    skeleton = [obj for obj in bpy.context.selected_objects if obj.type == 'ARMATURE']
    skeleton = skeleton[0]
    
    locations.clear()
    scale.clear()
    
    
    
    #if rollList:
    #    changeOrientation(skeleton)
    
    #rollList.clear()
    #axisList.clear()
    #headList.clear()
    #tailList.clear()
    #bpy.ops.object.mode_set(mode='EDIT')
    
    #for bone in skeleton.data.edit_bones:
        #axisMap[bone.name] = (bone.vector)
        #rollMap[bone.name] = (bone.roll)
        #rollList.append(bone.roll)
        #axisList.append(bone.vector)
        #headList.append(bone.head)
        #tailList.append(bone.tail)

    
    bpy.ops.object.mode_set(mode='POSE')    
    
    for  i, bone in enumerate(bones):
        #orientationList.append(bone.bone.MatrixFromAxisRoll(axisMap[bone.name],rollMap[bone.name]).to_3x3())
        
        rest = bone.bone.matrix_local.to_quaternion().to_matrix()
        parentRest = math.Matrix.Identity(3)
        if bone.parent:
            parentRest = bone.parent.bone.matrix_local.to_quaternion().to_matrix()
        
        smat = parentRest.inverted() @ rest
        
        bindList.append(smat.to_quaternion().to_matrix())
        #locations.append(bone.matrix.to_translation())
        #scale.append(bone.matrix.to_scale())

    
        
    for frame in sourceKeys:
        bpy.context.scene.frame_set(frame)
        tempRot = []
        for  bone in bones:
            rm = bone.matrix.to_quaternion().to_matrix()
            tempRot.append(rm) 
        rotationList.append(tempRot)
        
        
    
    
    
def selectSource():
    
    sourceSkeleton = [obj for obj in bpy.context.selected_objects if obj.type == 'ARMATURE']
    sourceSkeleton = sourceSkeleton[0]
    global sourceSkeletonName
    sourceSkeletonName = sourceSkeleton.name
     
    bpy.ops.object.mode_set(mode='POSE')
        
    
    
    
    
    
    for key in range(scene.frame_start, scene.frame_end+1):
        sourceKeys.append(key)
    
          
            
    for index, bone in enumerate(sourceSkeleton.pose.bones):
        sourcePoseBoneList.append(bone)
        sourceBoneNameList.append(bone.name)
        sourceIndexMap[bone.name]=index
        
    
    bpy.ops.object.mode_set(mode='EDIT')    
    for bone in sourceSkeleton.data.edit_bones:
        sourceEditBoneMap[bone.name]=bone
        
    sourceParentList.clear()
    bpy.ops.object.editmode_toggle()
    getRotandOrient(sourcePoseBoneList,sourceEditBoneMap, sourceRotationList,sourceOrientationList,sourceBindPoseBones,sourceSkeleton)
    #for boneIndex, bone in enumerate(sourcePoseBoneList):
        #sourceParentList.append(calcParentMatrices(boneIndex, True))
        
            
    

def selectTarget():
    
    
    targetSkeleton = [obj for obj in bpy.context.selected_objects if obj.type == 'ARMATURE']
    targetSkeleton = targetSkeleton[0]
    global targetSkeletonName
    targetSkeletonName = targetSkeleton.name
    
    changeOrientation(targetSkeleton)
    bpy.ops.object.mode_set(mode='POSE')
    
    for index, bone in enumerate(targetSkeleton.pose.bones):
        targetPoseBoneList.append(bone)
        targetBoneNameList.append(bone.name)
        targetIndexMap[bone.name]=index
        
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in targetSkeleton.data.edit_bones:
        targetEditBoneMap[bone.name]=bone
        
    bpy.ops.object.mode_set(mode='POSE')      
  
    targetParentList.clear()
    bpy.ops.object.editmode_toggle()
    getRotandOrient(targetPoseBoneList,targetEditBoneMap, targetRotationList,targetOrientationList,targetBindPoseBones, targetSkeleton)
    #for boneIndex, bone in enumerate(targetPoseBoneList):
        #targetParentList.append(calcParentMatrices(boneIndex, False))
        

        

            
def transfer():
    targetSkeleton = [obj for obj in bpy.context.selected_objects if obj.type == 'ARMATURE']
    targetSkeleton = targetSkeleton[0]
    bpy.data.objects[targetSkeletonName].location = bpy.data.objects[sourceSkeletonName].location
    bpy.ops.object.mode_set(mode='POSE')
    for frameIndex, frame in enumerate(sourceKeys):
        bpy.context.scene.frame_set(frame)
        for boneIndex, bone in enumerate(targetSkeleton.pose.bones):
            finaMat = calcRotMat(frameIndex, boneIndex)
            rot = finaMat.to_quaternion()
            t = bone.matrix.to_translation()
            s = bone.matrix.to_scale()
            bone.matrix = math.Matrix().LocRotScale(t, rot, s)
            bone.keyframe_insert(data_path="location", frame=frame)
            bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            bone.keyframe_insert(data_path="scale", frame=frame)
            
    
    
  

            
        
            
    

class Source(bpy.types.Operator):
    
    bl_idname = 'opr.object_source_operator'
    bl_label = 'Select Source'
    def execute(self, context):
        selectSource()  
        return {'FINISHED'}
    
class Target(bpy.types.Operator):
    
    bl_idname = 'opr.object_target_operator'
    bl_label = 'Select Target'
    def execute(self, context):
        selectTarget()  
        return {'FINISHED'}    
    
class Transfer(bpy.types.Operator):
    
    bl_idname = 'opr.object_transfer_operator'
    bl_label = 'Transfer'
    def execute(self, context):
        transfer()  
        return {'FINISHED'}
    
class panel(bpy.types.Panel):
    
    bl_idname = 'VIEW3D_PT_main_panel'
    bl_label = 'Panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        self.layout.label(text='Change the number of frames')
        self.layout.label(text='Select source first then target.')
        self.layout.operator(Source.bl_idname, text='Select Source')
        self.layout.operator(Target.bl_idname, text='Select Target')
        self.layout.operator(Transfer.bl_idname, text='Transfer')

CLASSES = [panel,Source,Target,Transfer]


def register():
    for klass in CLASSES:
        bpy.utils.register_class(klass)

def unregister():
    for klass in CLASSES:
        bpy.utils.unregister_class(klass)
    
    
if __name__ == '__main__':
    register()