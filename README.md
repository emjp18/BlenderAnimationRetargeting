# BlenderAnimationRetargeting
Retargets skeletons with the same structure but given different bindposes, you do not need to manually edit the bones of the target to match the source.
Requires you to edit the timeline for the proper amount of keyframes. And first click on the source then the target, as well as reboot the application after every use.
It assumes the source and target has the same amount of bones that match.
When clicking on source and target respectively the rotations for every frame and every bone is collected as well as the bind poses of every joint. The orientation is transferred through alot of complicated logic. After that the rotation is isolated then converted to a world space then target bone space and finally a matrix with the target bind pose has the rotation that is then applied to the bone. The root is also assumed to be at slot 0.
