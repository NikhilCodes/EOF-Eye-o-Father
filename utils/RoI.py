import cv2
import numpy as np
import selectivesearch

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from keras.models import load_model
from keras.applications.mobilenet_v2 import decode_predictions, MobileNetV2


model = load_model('MODEL/MobileNetV2.h5')
model.compile(optimizer='Adam',loss='categorical_crossentropy')
model._make_predict_function()

## UTILS
def box_is_almost_same(box1, box2):
    '''
    This function return `True` if it is almost half the size of other
    '''
    if ((box1[0]-box2[0])**2 + (box1[1]-box2[1])**2)**0.5 < ((box1[2]/2)**2 + (box2[2]/2)**2)**0.5:
        return True
    
    return False


##

def get_regions_with_detection(img):
    img_lbls,regions = selectivesearch.selective_search(img, scale=100, min_size=1600)

    candidates = set()
    for r in regions:
        x,y,w,h = r['rect']
        if w > 80 and h > 80:
            candidates.add(r['rect'])

    
    res = []
    for x,y,w,h in candidates:
        sub_img = cv2.resize(img[y:y+h, x:x+w], (224,224))
        #plt.imshow(sub_img/255)
        #plt.show()
        res.append(decode_predictions(model.predict(np.array([sub_img])/255), top=1)[0][0][1:]+((x,y,w,h),))
        #print(res[-1])

    res = sorted(res, key=lambda x: x[2][2]*x[2][3], reverse=True)

    final_res = list()
    for obj, proba, bbox in res:
        if proba > 0.7:
            DUPLICATE_FOUND = False
            for i in range(len(final_res)):
                if box_is_almost_same(final_res[i][2], bbox):
                    DUPLICATE_FOUND = True
                    if (final_res[i][1] < proba) and ([obj,proba,bbox] not in final_res):
                        final_res[i] = [obj,proba,bbox] 
                    
            if not DUPLICATE_FOUND:
                final_res.append([obj,proba,bbox])

    return final_res

