from collections import defaultdict

from .mc import Label,AbsRef,RelRef,Constant
from .instr import Instr, Reg


__all__ = [
    # Directives
    "L","AR","RR","C",
    # Registers
    "R0",   "R1",   "R2",   "R3",   "R4",   "R5",   "R6",   "R7",
    # Instructions
    "AND",  "ANDI", "OR",   "ORI",  "XOR",  "XORI", "CMP",  "CMPI",
    "ADD",  "ADDI", "ADC",  "ADCI", "SUB",  "SUBI", "SBC",  "SBCI",
    "SLL",  "SLLI", "ROL",  "ROLI", "RORI", "SRL",  "SRLI", "SRA",  "SRAI",
    "LD",   "LDR",  "ST",   "STR",  "LDX",  "LDXA", "STX",  "STXA",
    "MOV",  "MOVI", "MOVR", "XCHG",
    "STW",  "XCHW", "ADJW", "LDW",
    "J",    "JR",   "JRAL", "JVT",  "JST",  "JAL",  "NOP",
    "BGES", "BGEU", "BGTS", "BGTU", "BLES", "BLEU", "BLTS", "BLTU", "BEQ",  "BNE",
    "BZ",   "BNZ",  "BS",   "BNS",  "BC",   "BNC",  "BV",   "BNV",
    "BZ1",  "BZ0",  "BS1",  "BS0",  "BC1",  "BC0",  "BV1",  "BV0",
    "EXTI"
]


# Instruction formats
class F_RRR  (Instr): coding = "-----DDDAAA--BBB"; operands = "{rsd:R}, {ra:R}, {rb:R}"
class F_XRR  (Instr): coding = "-----000AAA--BBB"; operands = "{ra:R}, {rb:R}"
class F_RR3A (Instr): coding = "-----DDDAAA--iii"; operands = "{rsd:R}, {ra:R}, {imm:I3AL}"
class F_XR3A (Instr): coding = "-----000AAA--iii"; operands = "{ra:R}, {imm:I3AL}"
class F_RR3S (Instr): coding = "-----DDDAAA--iii"; operands = "{rsd:R}, {ra:R}, {imm:I3SR}"
class F_RR5  (Instr): coding = "-----DDDAAAiiiii"; operands = "{rsd:R}, {ra:R}, {imm:I5}"
class F_RR   (Instr): coding = "-----DDD---00BBB"; operands = "{rsd:R}, {rb:R}"
class F_XR   (Instr): coding = "-----000---00BBB"; operands = "{rb:R}"
class F_R5   (Instr): coding = "-----DDD---iiiii"; operands = "{rsd:R}, {imm:I5}"
class F_X5   (Instr): coding = "-----000---iiiii"; operands = "{imm:I5}"
class F_R8   (Instr): coding = "-----DDDiiiiiiii"; operands = "{rsd:R}, {imm:I8}"
class F_8    (Instr): coding = "--------iiiiiiii"; operands = "{imm:I8}"
class F_13   (Instr): coding = "---iiiiiiiiiiiii"; operands = "{imm:I13}"

# ALSRU opcodes
class M_RRR  (Instr): coding = "----0-----------"
class M_RRI  (Instr): coding = "----1-----------"
class C_LOGIC(Instr): coding = "0000------------"
class T_AND  (Instr): coding = "-----------00---"
class T_OR   (Instr): coding = "-----------01---"
class T_XOR  (Instr): coding = "-----------10---"
class T_CMP  (Instr): coding = "-----------11---"
class C_ARITH(Instr): coding = "0001------------"
class T_ADD  (Instr): coding = "-----------00---"
class T_ADC  (Instr): coding = "-----------01---"
class T_SUB  (Instr): coding = "-----------10---"
class T_SBC  (Instr): coding = "-----------11---"
class T_SBB  (Instr): coding = "-----------11---"
class C_SHIFT(Instr): coding = "0010------------"
class S_LEFT (Instr): coding = "-----------0----"
class S_RIGHT(Instr): coding = "-----------1----"
class S_IZERO(Instr): coding = "------------0---"
class S_IMSB (Instr): coding = "------------1---"
class T_SLL  (S_LEFT,  S_IZERO): pass
class T_ROL  (S_LEFT,  S_IMSB):  pass
class T_SRL  (S_RIGHT, S_IZERO): pass
class T_SRA  (S_RIGHT, S_IMSB):  pass

# Memory opcodes
class M_ABS  (Instr): coding = "----0-----------"
class M_REL  (Instr): coding = "----1-----------"; pc_rel_ops = {"imm"}
class M_LIT  (Instr): coding = "----1-----------"
class C_LD   (Instr): coding = "0100------------"
class C_ST   (Instr): coding = "0101------------"
class C_LDX  (Instr): coding = "0110------------"
class C_STX  (Instr): coding = "0111------------"
class C_MOVE (Instr): coding = "1000------------"

# Window opcodes
class C_STW  (Instr): coding = "10100---000-----"
class C_XCHW (Instr): coding = "10100---001-----"
class C_ADJW (Instr): coding = "10100---010-----"
class C_LDW  (Instr): coding = "10100---011-----"

# Jump opcodes
class C_JR   (Instr): coding = "10100---100-----"
class C_JRAL (Instr): coding = "10100---101-----"
class C_JVT  (Instr): coding = "10100---110-----"
class C_JST  (Instr): coding = "10100---111-----"; pc_rel_ops = {"imm"}
class C_JAL  (Instr): coding = "10101-----------"; pc_rel_ops = {"imm"}

# Conditional opcode
class M_FL0  (Instr): coding = "----0-----------"
class M_FL1  (Instr): coding = "----1-----------"
class C_JCOND(Instr): coding = "1011------------"; pc_rel_ops = {"imm"}
class T_Z    (Instr): coding = "-----000--------"
class T_S    (Instr): coding = "-----001--------"
class T_C    (Instr): coding = "-----010--------"
class T_V    (Instr): coding = "-----011--------"
class T_nCoZ (Instr): coding = "-----100--------"
class T_SxV  (Instr): coding = "-----101--------"
class T_SxVoZ(Instr): coding = "-----110--------"
class T_A    (Instr): coding = "-----111--------"

# Extended immediate opcode
class C_EXT  (Instr): coding = "110-------------"


# Directives
L = Label
AR = AbsRef
RR = RelRef
C = Constant

# Registers
R0, R1, R2, R3, R4, R5, R6, R7 = map(Reg, range(8))

# ALSRU instructions
class AND (C_LOGIC, M_RRR, T_AND,   F_RRR ): pass
class ANDI(C_LOGIC, M_RRI, T_AND,   F_RR3A): pass
class OR  (C_LOGIC, M_RRR, T_OR,    F_RRR ): pass
class ORI (C_LOGIC, M_RRI, T_OR,    F_RR3A): pass
class XOR (C_LOGIC, M_RRR, T_XOR,   F_RRR ): pass
class XORI(C_LOGIC, M_RRI, T_XOR,   F_RR3A): pass
class CMP (C_LOGIC, M_RRR, T_CMP,   F_XRR ): pass
class CMPI(C_LOGIC, M_RRI, T_CMP,   F_XR3A): pass

class ADD (C_ARITH, M_RRR, T_ADD,   F_RRR ): pass
class ADDI(C_ARITH, M_RRI, T_ADD,   F_RR3A): pass
class ADC (C_ARITH, M_RRR, T_ADC,   F_RRR ): pass
class ADCI(C_ARITH, M_RRI, T_ADC,   F_RR3A): pass
class SUB (C_ARITH, M_RRR, T_SUB,   F_RRR ): pass
class SUBI(C_ARITH, M_RRI, T_SUB,   F_RR3A): pass
class SBC (C_ARITH, M_RRR, T_SBC,   F_RRR ): pass
class SBCI(C_ARITH, M_RRI, T_SBC,   F_RR3A): pass

class SLL (C_SHIFT, M_RRR, T_SLL,   F_RRR ): pass
class SLLI(C_SHIFT, M_RRI, T_SLL,   F_RR3S): pass
class ROL (C_SHIFT, M_RRR, T_ROL,   F_RRR ): pass
class ROLI(C_SHIFT, M_RRI, T_ROL,   F_RR3S): pass
class SRL (C_SHIFT, M_RRR, T_SRL,   F_RRR ): pass
class SRLI(C_SHIFT, M_RRI, T_SRL,   F_RR3S): pass
class SRA (C_SHIFT, M_RRR, T_SRA,   F_RRR ): pass
class SRAI(C_SHIFT, M_RRI, T_SRA,   F_RR3S): pass

# Memory instructions
class LD  (C_LD,    M_ABS,          F_RR5 ): pass
class LDR (C_LD,    M_REL,          F_RR5 ): pass
class ST  (C_ST,    M_ABS,          F_RR5 ): pass
class STR (C_ST,    M_REL,          F_RR5 ): pass
class LDX (C_LDX,   M_ABS,          F_RR5 ): pass
class LDXA(C_LDX,   M_LIT,          F_R8  ): pass
class STX (C_STX,   M_ABS,          F_RR5 ): pass
class STXA(C_STX,   M_LIT,          F_R8  ): pass

# Move instructions
class MOVI(C_MOVE,  M_ABS,          F_R8  ): pass
class MOVR(C_MOVE,  M_REL,          F_R8  ): pass

# Window instructions
class STW (C_STW,                   F_XR  ): pass
class XCHW(C_XCHW,                  F_RR  ): pass
class ADJW(C_ADJW,                  F_X5  ): pass
class LDW (C_LDW,                   F_R5  ): pass

# Jump instructions
class J   (C_JCOND, M_FL1, T_A,     F_8   ): pass
class JR  (C_JR,                    F_R5  ): pass
class JRAL(C_JRAL,                  F_RR  ): pass
class JVT (C_JVT,                   F_R5  ): pass
class JST (C_JST,                   F_R5  ): pass
class JAL (C_JAL,                   F_R8  ): pass
class NOP (C_JCOND, M_FL0, T_A,     F_8   ): pass

# Conditional branch instructions
class BZ1 (C_JCOND, M_FL1, T_Z,     F_8   ): pass
class BZ0 (C_JCOND, M_FL0, T_Z,     F_8   ): pass
class BS1 (C_JCOND, M_FL1, T_S,     F_8   ): pass
class BS0 (C_JCOND, M_FL0, T_S,     F_8   ): pass
class BC1 (C_JCOND, M_FL1, T_C,     F_8   ): pass
class BC0 (C_JCOND, M_FL0, T_C,     F_8   ): pass
class BV1 (C_JCOND, M_FL1, T_V,     F_8   ): pass
class BV0 (C_JCOND, M_FL0, T_V,     F_8   ): pass

class BZ  (BZ1                            ): pass
class BNZ (BZ0                            ): pass
class BS  (BS1                            ): pass
class BNS (BS0                            ): pass
class BC  (BC1                            ): pass
class BNC (BC0                            ): pass
class BV  (BV1                            ): pass
class BNV (BV0                            ): pass

class BEQ (BZ1                            ): pass
class BGTS(C_JCOND, M_FL0, T_SxVoZ, F_8   ): pass
class BGTU(C_JCOND, M_FL0, T_nCoZ,  F_8   ): pass
class BGES(C_JCOND, M_FL0, T_SxV,   F_8   ): pass
class BGEU(BC1                            ): pass
class BLES(C_JCOND, M_FL1, T_SxVoZ, F_8   ): pass
class BLEU(C_JCOND, M_FL1, T_nCoZ,  F_8   ): pass
class BLTS(C_JCOND, M_FL1, T_SxV,   F_8   ): pass
class BLTU(BC0                            ): pass
class BNE (BZ0                            ): pass

# Extended immediate instruction
class EXTI(C_EXT,                   F_13  ): pass

# Synthetic instructions
def RORI(Rd, Ra, amount): return ROLI(Rd, Ra, 0 if amount == 0 else 16-amount)
def MOV(Rd, Rs): return AND(Rd, Rs, Rs)
def XCHG(Ra, Rb):
    if Ra == Rb:
        return []
    else:
        return [XOR(Ra, Ra, Rb), XOR(Rb, Rb, Ra), XOR(Ra, Ra, Rb)]
