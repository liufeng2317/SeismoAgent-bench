import torch
import torch.nn as nn

from .base import WaveformModel, WaveformPipeline


class DPPPicker(WaveformModel):
    def __init__(self, mode):
        super().__init__()

        self.mode = mode

        if self.mode == "P":
            """
            Custom LSTM removed for performance reasons.
            Could probably be fixed with JIT CustomLSTM.

            self.lstm1 = CustomLSTM(
                ActivationLSTMCell,
                1,
                100,
                bidirectional=True,
                recurrent_dropout=0.25,
                gate_activation=torch.sigmoid,
            )
            self.lstm2 = CustomLSTM(
                ActivationLSTMCell,
                200,
                160,
                bidirectional=True,
                recurrent_dropout=0.25,
                gate_activation=torch.sigmoid,
            )
            """
            self.lstm1 = nn.LSTM(1, 100, bidirectional=True)
            self.lstm2 = nn.LSTM(200, 160, bidirectional=True)
            self.dropout1 = nn.Dropout(0.2)
            self.dropout2 = nn.Dropout(0.35)
            self.fc1 = nn.Linear(320, 1)
        elif self.mode == "S":
            """
            See remark for P mode above

            self.lstm1 = CustomLSTM(
                ActivationLSTMCell,
                2,
                20,
                bidirectional=True,
                recurrent_dropout=0.25,
                gate_activation=torch.sigmoid,
            )
            self.lstm2 = CustomLSTM(
                ActivationLSTMCell,
                40,
                30,
                bidirectional=True,
                recurrent_dropout=0.25,
                gate_activation=torch.sigmoid,
            )
            """
            self.lstm1 = nn.LSTM(2, 20, bidirectional=True)
            self.lstm2 = nn.LSTM(40, 30, bidirectional=True)
            self.dropout1 = nn.Dropout(0.25)
            self.dropout2 = nn.Dropout(0.45)
            self.fc1 = nn.Linear(60, 1)

        self.activation = torch.sigmoid

    def forward(self, x):
        # Permute shapes to match LSTM  --> (seq, batch, channels)

        x = x.permute(2, 0, 1)  # (batch, channels, seq) --> (seq, batch, channels)
        x = self.lstm1(x)[0]
        x = self.dropout1(x)
        x = self.lstm2(x)[0]
        x = self.dropout2(x)
        x = x.permute(1, 0, 2)  # (seq, batch, channels) --> (batch, seq, channels)

        # keras TimeDistributed layer is applied by:
        # -> reshaping from (batch, sequence, *) to (batch * sequence, *)
        # -> then applying the layer,
        # -> then reshaping back to (batch, sequence, *)
        #
        shape_save = x.shape
        x = x.reshape((-1,) + x.shape[2:])

        x = self.activation(self.fc1(x))
        x = x.reshape(shape_save[:2] + (1,))
        x = x.squeeze(-1)

        return x
