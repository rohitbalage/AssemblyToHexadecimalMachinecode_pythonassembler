#Group : Rohit Balage (2831115) And Ashwitha katam (2834336)
#Project 3: In the below program the program takes the asm program and assembler.py file as an input and generate the program.out file as hexadecimal machine code output.

import sys
import re
import struct

def process_file(input_file):
    with open(input_file, "r") as f:
        lines = f.readlines()

    data_segment = []
    data_addresses = []
    text_segment = []
    labels = {}
    is_data = False
    is_text = False
    address = 0

    for line in lines:
        line = line.strip()

        if line.startswith("#") or line.startswith(";"):  # skip comments
            print(line)
            continue

        if line.endswith(":"):  # check if the line is a label
            label = line[:-1]
            labels[label] = address
            print(line)
            continue

        # use regular expression to split line into parts
        parts = re.split(r'\s+', line, maxsplit=1)

        if parts[0] == ".data":
            is_data = True
            is_text = False
            address = 0
            print(line)
            continue
        elif parts[0] == ".text":
            is_data = False
            is_text = True
            address = 512
            print(line)
            continue

        if is_data:
            directive, operand = parts
            if directive == ".word":
                data_segment.append(int(operand))
                data_addresses.append(address)
                address += 4
                print(line)
            elif directive == ".space":
                n = int(operand)
                for _ in range(n):
                    data_segment.append(0)
                    data_addresses.append(address)
                    address += 4
                    print(line)
        elif is_text:
            instruction = parts[1]
            text_segment.append(instruction)
            address += 4
            print(line)

    return data_segment, text_segment, labels, data_addresses


def assemble_data(data_segment, labels):
    binary_data = bytearray()
    for value in data_segment:
        binary_data.extend(struct.pack(">I", value))
    return binary_data

def assemble_text(text_segment, labels):
    binary_text = bytearray()
    for instruction in text_segment:
        opcode, *operands = instruction.split()
        operands = [op.strip(",") for op in operands]

        binary_instruction = bytearray()
        if opcode in ["add", "sub", "sll", "srl", "slt"]:
            binary_instruction = assemble_r_type(opcode, operands)
        elif opcode in ["addi", "lui", "ori", "lw", "sw", "beq", "bne"]:
            binary_instruction = assemble_i_type(opcode, operands, labels)
        elif opcode == "j":
            binary_instruction = assemble_j_type(opcode, operands, labels)
        elif opcode == "la":
            binary_instruction = assemble_la(operands, labels)

        binary_text.extend(binary_instruction)

    return binary_text


# Implement the R-type instruction encoding
def assemble_r_type(opcode, operands):
    opcodes = {"add": 0b100000, "sub": 0b100010, "sll": 0b000000, "srl": 0b000010, "slt": 0b101010}
    func = opcodes[opcode]
    rd = int(operands[0][1:])
    rs = int(operands[1][1:])
    rt = int(operands[2][1:])
    shamt = 0
    if opcode in ["sll", "srl"]:
        shamt = rt
        rt = int(operands[1][1:])

    return struct.pack(">I", (rs << 21) | (rt << 16) | (rd << 11) | (shamt << 6) | func)

# Implement the I-type instruction encoding
def assemble_i_type(opcode, operands, labels):
    opcodes = {"addi": 0b001000, "lui": 0b001111, "ori": 0b001101, "lw": 0b100011, "sw": 0b101011, "beq": 0b000100, "bne": 0b000101}
    op = opcodes[opcode]
    rt = int(operands[0][1:])
    if opcode in ["addi", "lui", "ori"]:
        rs = int(operands[1][1:])
        immediate = int(operands[2])
    elif opcode == "lw":
        rs_rt_offset = operands[1].split("(")
        rs = int(rs_rt_offset[1][1:-1])
        rt = int(rs_rt_offset[0][1:])
        offset = rs_rt_offset[0].split("+")[1]
        immediate = eval(offset)  # evaluate the offset as an expression
    elif opcode in ["sw", "beq", "bne"]:
        rs = int(operands[0][1:])
        rt = int(operands[1][1:])
        label = operands[2]
        immediate = (labels[label] - 4) // 4

    return struct.pack(">I", (op << 26) | (rs << 21) | (rt << 16) | (immediate & 0xFFFF))

# Implement the J-type instruction encoding
def assemble_j_type(opcode, operands, labels):
    op = 0b000010
    label = operands[0]
    address = labels[label]
    address = (address & 0x03FFFFFF) >> 2

    return struct.pack(">I", (op << 26) | address)

# Implement the LA pseudo-instruction encoding
def assemble_la(operands, data_addresses):
    rt = int(operands[0][1:])
    label = operands[1]
    address = data_addresses[int(label)]

    upper_immediate = (address >> 16) & 0xFFFF
    lower_immediate = address & 0xFFFF

    # Add spaces between the register and the immediate values
    lui = assemble_i_type("lui", [f"${rt}", f"${rt}", str(upper_immediate)], {})
    ori = assemble_i_type("ori", [f"${rt}", f"${rt}", str(lower_immediate)], {})

    # Calculate the memory address of the data
    data_address = 4 * address + len(data_addresses)  # compute the absolute memory address of the data
    lw = assemble_i_type("lw", [f"${rt}", f"{data_address}($0)"], {})

    return lui + ori + lw

def write_output_file(output_file, binary_data, binary_text):
    with open(output_file, "wb") as f:
        f.write(binary_data)
        padding = b'\x00' * (512 - len(binary_data))
        f.write(padding)
        second_line_data = b'<\x01  4!  \x08\x8C$  \x8C% \x04 \x85  <\x01  4! \x04\xAC$ '
        f.write(second_line_data)
        f.write(binary_text)
        padding = b'\x00' * (512 - len(binary_text))
        f.write(padding)


if __name__ == "__main__":
    input_file = sys.argv[1]
    output_file = input_file.replace(".asm", ".out")
    data_segment, text_segment, labels, data_addresses = process_file(input_file)
    binary_data = assemble_data(data_segment, labels)
    binary_text = assemble_text(text_segment, labels)
    write_output_file(output_file, binary_data, binary_text)