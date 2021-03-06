import json
import os
import cv2
import copy
import tkinter as tk
import tkinter.filedialog as fd
from shutil import copy as shutilcopy

def reorder_keypoints(keypoints):
        #keypoint correspondance list e.g. cList[5] = 10 means that the 5th keypoint in the desired format corresponds to the 10th in the raw format
        cList = [0, 16, 15, 18, 17, 5, 2, 6, 3, 7, 4, 12, 9, 13, 10, 14, 11]
        #https://github.com/CMU-Perceptual-Computing-Lab/openpose/blob/master/doc/02_output.md#ui-and-visual-output

        reordered_keypoints = []
        for i in range(len(cList)):
            #note that keypoints is a list in the following pattern [x,y,confidence, x, y, confidence, ...]
            #for coco the format is the same except the order of keypoints is different, and we use a status 0,1,2 instead of confidence (not used for us)
            for j in range(3):
                if j==2:
                    if keypoints[cList[i]*3+j] > 0.3:
                        reordered_keypoints.append(2)#status = 2 for inference (visible)
                    elif keypoints[cList[i]*3+j] > 0.15:
                        reordered_keypoints.append(1)#status = 1 for inference (hidden)
                    else:
                        reordered_keypoints.append(0)#status = 0 (unknown)
                else:
                    reordered_keypoints.append(keypoints[cList[i]*3+j])
        return reordered_keypoints

def json_reformatter(raw_path, template_path, img_path, output_path):

    #load template
    with open(template_path) as f:
        templateDict = json.load(f)

    reformattedDict = {}
    reformattedDict["categories"] = templateDict["categories"]
    reformattedDict["images"] = []
    reformattedDict["annotations"] = []
    #find json file


    img_id = 0
    anno_id = 0

    for file in os.listdir(raw_path):
        if file.endswith(".json"):
            with open(os.path.join(raw_path, file)) as f:#each raw json file corresponds to an image
                jsonDict = json.load(f)
            assert "people" in jsonDict, "No person detected in "+file[:-15]
            is_image_field_set = False
            for person in jsonDict["people"]:
                if not is_image_field_set:
                    #get template default key-values
                    reformattedDict["images"] = reformattedDict["images"]+copy.deepcopy(templateDict["images"])
                    #insert file info
                    ##file name
                    img_ext = ""
                    if file[:-15]+".jpg" in os.listdir(img_path):
                        img_ext = ".jpg"
                    elif file[:-15]+".png" in os.listdir(img_path):
                        img_ext = ".png"
                    assert img_ext == ".jpg" or img_ext == ".png", "Cannot find jpg or png image named"+file[1::-15]
                    reformattedDict["images"][-1]["file_name"] = file[:-15] + img_ext
                    ##image dimensions
                    reformattedDict["images"][-1]["height"], reformattedDict["images"][-1]["width"], _ = cv2.imread(os.path.join(img_path,file[:-15]+img_ext)).shape
                    ##image_id
                    reformattedDict["images"][-1]["id"] = file[:-15]
                    is_image_field_set = True
                #get template default key-values
                reformattedDict["annotations"] = reformattedDict["annotations"]+copy.deepcopy(templateDict["annotations"])
                ##image id
                reformattedDict["annotations"][-1]["image_id"] = file[:-15]
                ##re-ordered keypoints to match coco format
                reformattedDict["annotations"][-1]["keypoints"] = reorder_keypoints(person["pose_keypoints_2d"])
                ##annotation id
                anno_id += 1
                reformattedDict["annotations"][-1]["id"] = anno_id

    with open(os.path.join(output_path, "reformatted"+'.json'), 'w') as f:
        json.dump(reformattedDict, f)
   
def save_seg(img_dict, output_path, isKeepGroup=False):
    for image_file, segmented_persons_imgs in img_dict.items():
        i = 0
        for img in segmented_persons_imgs:
            i+=1
            if isKeepGroup:
                cv2.imwrite(os.path.join(output_path, image_file+"_grouped.png"), img)
            else:
                cv2.imwrite(os.path.join(output_path, image_file+"_"+str(i)+".png"), img)

def get_input_paths():
    root = tk.Tk()
    files = fd.askopenfilenames(parent=root, title='Choose a file')
    root.destroy()
    return files

def clear_folder(path):
    #clear past files
    for file in os.listdir(path):
        os.remove(os.path.join(path, file))

def create_output_dir(path, isSaveMasks=False):
    output_path = os.path.join(path,"output")
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    if isSaveMasks:
        masks_output_path = os.path.join(path, "output", "masks")
        if not os.path.exists(masks_output_path):
            os.makedirs(masks_output_path)
    else:
        masks_output_path = ""
    return output_path, masks_output_path

def copy_files(input_paths, output_path):
    for path in input_paths:
        shutilcopy(path, output_path)