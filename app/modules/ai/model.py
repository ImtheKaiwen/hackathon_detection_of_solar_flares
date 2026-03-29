import torch
import torch.nn as nn
import torch.nn.functional as F

class Attention(nn.Module):
    def __init__(self, hidden_dim):
        super(Attention, self).__init__()
        self.attention = nn.Linear(hidden_dim, 1, bias=False)

    def forward(self, lstm_out):
        attn_scores = self.attention(lstm_out)
        attn_weights = F.softmax(attn_scores, dim=1) 
        context_vector = torch.sum(attn_weights * lstm_out, dim=1) 
        return context_vector, attn_weights

class SolarFlarePredictorModel(nn.Module):
    def __init__(self, input_dim, hidden_dim, num_layers, dropout_rate=0.3):
        super(SolarFlarePredictorModel, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, 
                            batch_first=True, 
                            dropout=dropout_rate if num_layers > 1 else 0)
        
        self.attention = Attention(hidden_dim)
        self.fc1 = nn.Linear(hidden_dim, 32)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(32, 1) 
        self.sigmoid = nn.Sigmoid() 
        
    def forward(self, x):
        lstm_out, (h_n, c_n) = self.lstm(x)
        context_vector, attn_weights = self.attention(lstm_out)
        out = self.fc1(context_vector)
        out = self.relu(out)
        out = self.dropout(out)
        out = self.fc2(out)
        olasilik = self.sigmoid(out)
        return olasilik, attn_weights