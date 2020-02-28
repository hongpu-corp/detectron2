#! /bin/bash
pip install fire && python3 voc2coco.py voc2coco train_data/xml instances_train2017.json && python3 train_net.py --config-file /home/appuser/pai_detectron2/Base-RCNN-FPN.yaml OUTPUT_DIR /home/appuser/pai_detectron2/output/models | tee /home/appuser/pai_detectron2/output/logs/log.txt 