# realbasicvsr_config.py

model = dict(
    type='BasicVSR',
    generator=dict(
        type='RealBasicVSR',
        mid_channels=64,
        num_blocks=30,
        spynet_pretrained=None,
        upscale_factor=4,
        hr_in=True
    ),
    pixel_loss=dict(type='CharbonnierLoss', loss_weight=1.0, reduction='mean')
)

test_cfg = dict(metrics=['PSNR', 'SSIM'])
