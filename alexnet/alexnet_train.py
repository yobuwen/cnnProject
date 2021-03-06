# -*- coding: utf-8 -*-
"""
pycharm Editor

"""
import os
import json

import torch
import torch.nn as nn
from torchvision import transforms, datasets, utils
import torchvision
import matplotlib.pyplot as plt
import numpy as np
import torch.optim as optim
from tqdm import tqdm#用于生产进度条
import time

from alexnet_model import AlexNet


def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    print("using {} device.".format(device))

    data_transform = {
        "train": transforms.Compose([transforms.RandomResizedCrop(224),#随机裁剪
                                     transforms.RandomHorizontalFlip(),#翻转
                                     transforms.ToTensor(),
                                     transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))]),
        "val": transforms.Compose([transforms.Resize((224, 224)),  # cannot 224, must (224, 224)
                                   transforms.ToTensor(),
                                   transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))])}

    # 自定义图像数据集时使用
    # data_root = os.path.abspath(os.path.join(os.getcwd(), "../.."))  # get data root path
    # image_path = os.path.join(data_root, "data_set", "flower_data")  # flower data set path
    # assert os.path.exists(image_path), "{} path does not exist.".format(image_path)
    # train_dataset = datasets.ImageFolder(root=os.path.join(image_path, "train"),
    #                                      transform=data_transform["train"])
    # train_num = len(train_dataset)
    #
    # # {'daisy':0, 'dandelion':1, 'roses':2, 'sunflower':3, 'tulips':4}
    # flower_list = train_dataset.class_to_idx
    # cla_dict = dict((val, key) for key, val in flower_list.items())
    # # write dict into json file
    # json_str = json.dumps(cla_dict, indent=4)
    # with open('class_indices.json', 'w') as json_file:
    #     json_file.write(json_str)
    #
    # batch_size = 32
    # nw = min([os.cpu_count(), batch_size if batch_size > 1 else 0, 8])  # number of workers
    # print('Using {} dataloader workers every process'.format(nw))
    #
    # train_loader = torch.utils.data.DataLoader(train_dataset,
    #                                            batch_size=batch_size, shuffle=True,
    #                                            num_workers=nw)
    #
    # validate_dataset = datasets.ImageFolder(root=os.path.join(image_path, "val"),
    #                                         transform=data_transform["val"])
    # val_num = len(validate_dataset)
    # validate_loader = torch.utils.data.DataLoader(validate_dataset,
    #                                               batch_size=4, shuffle=False,
    #                                               num_workers=nw)
    #
    # print("using {} images for training, {} images for validation.".format(train_num,
    #                                                                        val_num))
    # test_data_iter = iter(validate_loader)
    # test_image, test_label = test_data_iter.next()
    #
    # def imshow(img):
    #     img = img / 2 + 0.5  # unnormalize
    #     npimg = img.numpy()
    #     plt.imshow(np.transpose(npimg, (1, 2, 0)))
    #     plt.show()
    #
    # print(' '.join('%5s' % cla_dict[test_label[j].item()] for j in range(4)))
    # imshow(utils.make_grid(test_image))

    train_set = torchvision.datasets.CIFAR10(root='./data', train=True, download=False, transform=data_transform["train"])
    train_loader = torch.utils.data.DataLoader(train_set, batch_size=500, shuffle=True, num_workers=12)

    val_set = torchvision.datasets.CIFAR10(root='./data', train=False, download=False, transform=data_transform["val"])
    val_loader = torch.utils.data.DataLoader(val_set, batch_size=500, shuffle=False, num_workers=0)
    val_num = len(val_set)

    net = AlexNet(num_classes=10, init_weights=True)

    # load model weights
    weights_path = "./AlexNet.pth"
    assert os.path.exists(weights_path), "file: '{}' dose not exist.".format(weights_path)
    net.load_state_dict(torch.load(weights_path))

    net.to(device)
    loss_function = nn.CrossEntropyLoss()
    # pata = list(net.parameters())
    optimizer = optim.Adam(net.parameters(), lr=0.0002)

    epochs = 50
    save_path = './AlexNet.pth'
    best_acc = 0.0
    train_steps = len(train_loader)
    for epoch in range(epochs):
        # train
        net.train()#允许使用dropout方法
        running_loss = 0.0
        # t1 = time.perf_counter()
        train_bar = tqdm(train_loader)
        for step, data in enumerate(train_bar):
            images, labels = data
            optimizer.zero_grad()
            outputs = net(images.to(device))
            loss = loss_function(outputs, labels.to(device))
            loss.backward()
            optimizer.step()

            # print statistics
            running_loss += loss.item()

            train_bar.desc = "train epoch[{}/{}] loss:{:.3f}".format(epoch + 1, epochs, loss)#在进度条前加上特定内容

        # print( time.perf_counter() - t1)

        # validate
        net.eval()#disable使用dropout方法
        acc = 0.0  # accumulate accurate number / epoch
        with torch.no_grad():
            val_bar = tqdm(val_loader)
            for val_data in val_bar:
                val_images, val_labels = val_data
                outputs = net(val_images.to(device))
                predict_y = torch.max(outputs, dim=1)[1]
                acc += torch.eq(predict_y, val_labels.to(device)).sum().item()

        val_accurate = acc / val_num
        print('[epoch %d] train_loss: %.3f  val_accuracy: %.3f' %
              (epoch + 1, running_loss / train_steps, val_accurate))

        if val_accurate > best_acc:
            best_acc = val_accurate
            torch.save(net.state_dict(), save_path)

    print('Finished Training')


if __name__ == '__main__':
    main()
