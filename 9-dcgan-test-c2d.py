import matplotlib.pyplot as plt
import numpy as np
import os 
from pathlib import Path
import pickle
import sys

import torch
import torch.nn as nn
import torchvision.utils as vutils

def test_dcgan(local=False):

    results_dir = Path('results')

    if not results_dir.exists():
        results_dir.mkdir()

    os.system("wget https://www.dropbox.com/s/p3pjgmpiki7w0ur/netG.pth")

    weights_path = Path("netG.pth")

    nc = 3
    nz = 100
    ngf = 64
    ngpu = 1

    # Decide which device we want to run on
    device = torch.device("cuda:0" if (torch.cuda.is_available() and ngpu > 0) else "cpu")

    # Generator Code
    class Generator(nn.Module):
        def __init__(self, ngpu):
            super(Generator, self).__init__()
            self.ngpu = ngpu
            self.main = nn.Sequential(
                # input is Z, going into a convolution
                nn.ConvTranspose2d( nz, ngf * 8, 4, 1, 0, bias=False),
                nn.BatchNorm2d(ngf * 8),
                nn.ReLU(True),
                # state size. (ngf*8) x 4 x 4
                nn.ConvTranspose2d(ngf * 8, ngf * 4, 4, 2, 1, bias=False),
                nn.BatchNorm2d(ngf * 4),
                nn.ReLU(True),
                # state size. (ngf*4) x 8 x 8
                nn.ConvTranspose2d( ngf * 4, ngf * 2, 4, 2, 1, bias=False),
                nn.BatchNorm2d(ngf * 2),
                nn.ReLU(True),
                # state size. (ngf*2) x 16 x 16
                nn.ConvTranspose2d( ngf * 2, ngf, 4, 2, 1, bias=False),
                nn.BatchNorm2d(ngf),
                nn.ReLU(True),
                # state size. (ngf) x 32 x 32
                nn.ConvTranspose2d( ngf, nc, 4, 2, 1, bias=False),
                nn.Tanh()
                # state size. (nc) x 64 x 64
            )

        def forward(self, input):
            return self.main(input)

    # Create the generator
    netG = Generator(ngpu).to(device)

    # Handle multi-gpu if desired
    if (device.type == 'cuda') and (ngpu > 1):
        netG = nn.DataParallel(netG, list(range(ngpu)))

    netG.load_state_dict(torch.load(weights_path))

    netG.eval()

    # Create batch of latent vectors that we will use to visualize
    #  the progression of the generator
    fixed_noise = torch.randn(1, nz, 1, 1, device=device)

    with torch.no_grad():
        img = netG(fixed_noise).detach().cpu()

    def denormalize_image(image):
        """Reverse to normalize_image() function"""
        max_ = image.max()
        min_ = image.min()
        return (image - min_)/(max_ - min_)

    img = denormalize_image(img)

    img = img.squeeze().permute(1,2,0)

    filename = results_dir / 'test.pickle' if local else "/data/outputs/result"

    with open(filename, 'wb') as pickle_file:
        print(f"Pickling results in {filename}")
        pickle.dump(img, pickle_file)

if __name__ == "__main__":
    local = (len(sys.argv) == 2 and sys.argv[1] == "local")
    test_dcgan(local)