import torch

from modules.diffusion.ddpm import MultiVarianceDiffusion
from utils.hparams import hparams


class ParameterAdaptorModule(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.predict_energy = hparams.get('predict_energy', False)
        self.predict_breathiness = hparams.get('predict_breathiness', False)
        self.variance_prediction_list = []
        if self.predict_energy:
            self.variance_prediction_list.append('energy')
        if self.predict_breathiness:
            self.variance_prediction_list.append('breathiness')
        self.predict_variances = len(self.variance_prediction_list) > 0

    def build_adaptor(self):
        ranges = []
        clamps = []

        if self.predict_energy:
            ranges.append((
                10. ** (hparams['energy_db_min'] / 20.),
                10. ** (hparams['energy_db_max'] / 20.)
            ))
            clamps.append((0., 1.))

        if self.predict_breathiness:
            ranges.append((
                10. ** (hparams['breathiness_db_min'] / 20.),
                10. ** (hparams['breathiness_db_max'] / 20.)
            ))
            clamps.append((0., 1.))

        variances_hparams = hparams['variances_prediction_args']
        return MultiVarianceDiffusion(
            ranges=ranges,
            clamps=clamps,
            repeat_bins=variances_hparams['repeat_bins'],
            timesteps=hparams['timesteps'],
            k_step=hparams['K_step'],
            denoiser_type=hparams['diff_decoder_type'],
            denoiser_args=(
                variances_hparams['residual_layers'],
                variances_hparams['residual_channels']
            )
        )

    def collect_variance_inputs(self, **kwargs) -> list:
        return [kwargs.get(name) for name in self.variance_prediction_list]

    def collect_variance_outputs(self, variances: list | tuple) -> dict:
        return {
            name: pred
            for name, pred in zip(self.variance_prediction_list, variances)
        }