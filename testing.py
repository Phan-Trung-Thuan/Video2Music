import torch
import torch.nn as nn
import torch.nn.functional as F

SEPERATOR = "==========="

def reshape_tensor(tensor):
    return tensor.reshape(tensor.shape[0] * tensor.shape[1], -1)

def reshape_tensor_2(tensor):
    return tensor.permute(0,2,1)

def main():
    ce_loss = nn.CrossEntropyLoss()
    bce_loss = nn.BCEWithLogitsLoss()

    print("Batch size = 1") 
    input = torch.randn(1, 50, 128, requires_grad=True)
    target_ce = torch.empty(1, 50, dtype=torch.long).random_(1)
    targe_bce = torch.empty(1, 50, 128).random_(1)
    input_2 = input.detach().clone()

    print("Original: ") 
    output_ce = ce_loss(reshape_tensor(input), target_ce.flatten())
    output_bce = bce_loss(reshape_tensor(input), reshape_tensor(targe_bce))    
    print("ce_loss = ", output_ce, "bce_loss = ", output_bce)

    print(SEPERATOR)

    print("Modify: ")
    output_ce = ce_loss(reshape_tensor_2(input_2), target_ce)
    output_bce = bce_loss(reshape_tensor_2(input_2), reshape_tensor_2(targe_bce))    
    print("ce_loss = ", output_ce, "bce_loss = ", output_bce)

    print(SEPERATOR)
    print(SEPERATOR)

    print("Batch size = 16")
    input = torch.randn(16, 50, 128, requires_grad=True)
    target_ce = torch.empty(16, 50, dtype=torch.long).random_(1)
    targe_bce = torch.empty(16, 50, 128).random_(1)
    input_2 = input.detach().clone()


    print("Original: ") 
    output_ce = ce_loss(reshape_tensor(input), target_ce.flatten())
    output_bce = bce_loss(reshape_tensor(input), reshape_tensor(targe_bce))    
    print("ce_loss = ", output_ce, "bce_loss = ", output_bce)

    print(SEPERATOR)

    print("Modify: ")
    output_ce = ce_loss(reshape_tensor_2(input_2), target_ce)
    output_bce = bce_loss(reshape_tensor_2(input_2), reshape_tensor_2(targe_bce))    
    print("ce_loss = ", output_ce, "bce_loss = ", output_bce)


if __name__ == "__main__":
    main()
