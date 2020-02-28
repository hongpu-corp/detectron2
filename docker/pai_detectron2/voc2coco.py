# -*- coding: utf-8 -*-
import os
import os.path as osp
import logging
import xml.etree.ElementTree as ET  
import glob
import json
import collections
import fire

from hp_utils import ConfigYaml


def file_basename(filename, with_ext=True):
    bn = osp.basename(filename)
    if not with_ext:
        bn = osp.splitext(bn)[0]
    return bn

class VOC2COCO:

    def __init__(self, PRE_DEFINE_CATEGORIES):
        self.PRE_DEFINE_CATEGORIES = PRE_DEFINE_CATEGORIES
        self.START_BOUNDING_BOX_ID = 1

    def get(self, root, name):
        vars = root.findall(name)
        return vars

    def get_and_check(self, root, name, length):
        vars = root.findall(name)
        if len(vars) == 0:
            raise NotImplementedError('Can not find %s in %s.' % (name, root.tag))
        if 0 < length != len(vars):
            raise NotImplementedError('The size of %s is supposed to be %d, but is %d.' % (name, length, len(vars)))
        if length == 1:
            vars = vars[0]
        return vars


    def convert(self, xml_dir, json_file):
        xmls = glob.glob(osp.join(xml_dir,'*.xml'))
        xml_list = [file_basename(x, False) for x in xmls]
        json_dict = {"images": [], "type": "instances", "annotations": [],
                     "categories": []}
        categories = self.PRE_DEFINE_CATEGORIES
        bnd_id = self.START_BOUNDING_BOX_ID
        image_id = 0
        for line in xml_list:
            print("Processing %s" % (line))
            xml_f = os.path.join(xml_dir, line)
            tree = ET.parse(xml_f + '.xml')
            root = tree.getroot()
            filename = self.get(root, 'filename')
            
            if len(filename) == 1:
                filename = os.path.basename(filename[0].text)
            elif len(filename) == 0:
                path = self.get_and_check(root, 'path', 1).text
                filename = os.path.basename(path)
            else:
                raise NotImplementedError('%d paths found in %s' % (len(path), line))
            # The filename must be a number
            image_id += 1
            size = self.get_and_check(root, 'size', 1)
            width = int(self.get_and_check(size, 'width', 1).text)
            height = int(self.get_and_check(size, 'height', 1).text)
            image = {'file_name': filename, 'height': height, 'width': width,
                     'id': image_id}
            json_dict['images'].append(image)
            ## Cruuently we do not support segmentation
            #  segmented = get_and_check(root, 'segmented', 1).text
            #  assert segmented == '0'
            for obj in self.get(root, 'object'):
                category = self.get_and_check(obj, 'name', 1).text
                if category not in categories:
                    new_id = len(categories)
                    categories[category] = new_id
                category_id = categories[category]
                bndbox = self.get_and_check(obj, 'bndbox', 1)
                xmin = int(self.get_and_check(bndbox, 'xmin', 1).text) - 1
                ymin = int(self.get_and_check(bndbox, 'ymin', 1).text) - 1
                xmax = int(self.get_and_check(bndbox, 'xmax', 1).text)
                ymax = int(self.get_and_check(bndbox, 'ymax', 1).text)
                assert (xmax > xmin)
                assert (ymax > ymin)
                o_width = abs(xmax - xmin)
                o_height = abs(ymax - ymin)
                ann = {'area': o_width * o_height, 'iscrowd': 0, 'image_id':
                    image_id, 'bbox': [xmin, ymin, o_width, o_height],
                       'category_id': category_id, 'id': bnd_id, 'ignore': 0,
                       'segmentation': []}
                json_dict['annotations'].append(ann)
                bnd_id = bnd_id + 1

        for cate, cid in categories.items():
            cat = {'supercategory': 'none', 'id': cid, 'name': cate}
            json_dict['categories'].append(cat)
        with  open(json_file, 'w') as json_fp:
            json_str = json.dumps(json_dict)
            json_fp.write(json_str)

def voc2coco(vocxml_dir, save_coco_path):

    pc = ConfigYaml('pai_config.yaml')
    classes = pc.get_config("MODEL.CLASSES", [])
    classes_list = []
    for idx in range(len(classes)):
        classes_list.append( (classes[idx], idx + 1) )
    PRE_DEFINE_CATEGORIES = collections.OrderedDict( classes_list )

    # 执行voc2coco
    voc2coco = VOC2COCO(PRE_DEFINE_CATEGORIES)
    voc2coco.convert(vocxml_dir, save_coco_path)

if __name__=='__main__':
    fire.Fire({
        'voc2coco':voc2coco
    })

