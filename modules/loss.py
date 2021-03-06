# coding=utf8
import torch
import torch.nn as nn
from torch.autograd import Variable
import torch.nn.functional as F

def sequence_mask(sequence_length, max_len=None):
    if max_len is None:
        max_len = sequence_length.data.max()
    batch_size = sequence_length.size(0)
    seq_range = torch.arange(0, max_len).long()
    seq_range_expand = seq_range.unsqueeze(0).expand(batch_size, max_len)
    seq_range_expand = Variable(seq_range_expand)
    if sequence_length.is_cuda:
        seq_range_expand = seq_range_expand.cuda()
    seq_length_expand = (sequence_length.unsqueeze(1)
                         .expand_as(seq_range_expand))
    return seq_range_expand < seq_length_expand

    
class MaskedCrossEntropyLoss(nn.Module):
    def __init__(self, gpu=False):
        super(MaskedCrossEntropyLoss, self).__init__()
        self.gpu = gpu

    def forward(self, logits, target, tgt_lens):
        length = Variable(torch.LongTensor(tgt_lens))
        if self.gpu:
            length = length.cuda()

        # logits_flat: (batch * max_len, num_classes)
        logits_flat = logits.view(-1, logits.size(-1))
        # log_probs_flat: (batch * max_len, num_classes)
        log_probs_flat = F.log_softmax(logits_flat, dim=1)


        # target_flat: (batch * max_len, 1)
        target_flat = target.view(-1, 1)
        # losses_flat: (batch * max_len, 1)
        losses_flat = -torch.gather(log_probs_flat, dim=1, index=target_flat)

        # losses: (batch, max_len)
        losses = losses_flat.view(*target.size())
        # mask: (batch, max_len)
        mask = sequence_mask(sequence_length=length, max_len=target.size(0)).transpose(0, 1)
        losses = losses * mask.float()

        loss = losses.sum() / length.float().sum()
        return loss
