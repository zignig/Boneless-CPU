from nmigen import *

from ..arch.opcode_v3 import *
from .control import *


__all__ = ["ImmediateDecoder", "InstructionDecoder"]


def decode(m, v):
    d = Signal.like(v, src_loc_at=1)
    m.d.comb += d.eq(v)
    return d


class ImmediateDecoder(Elaboratable):
    IMM3_TABLE_AL = Array([0x0000, 0x0001, 0x8000, 0, # ?
                           0x00ff, 0xff00, 0x7fff, 0xffff])
    IMM3_TABLE_SR = Array([8, 1, 2, 3, 4, 5, 6, 7])

    class Table(ControlEnum):
        AL    = 0b0
        SR    = 0b1

    class Width(ControlEnum):
        IMM3  = 0b00
        IMM5  = 0b01
        IMM8  = 0b10
        IMM16 = 0b11

    def __init__(self):
        self.i_pc    = Signal(16)
        self.i_insn  = Signal(16)
        self.o_imm16 = Signal(16)

        self.c_exti  = Signal()
        self.c_table = self.Table.signal()
        self.c_width = self.Width.signal()
        self.c_addpc = Signal()

        self.r_ext13 = Signal(13)

    def elaborate(self, platform):
        m = Module()

        i_insn  = self.i_insn

        d_imm3  = decode(m, i_insn[0:3])
        d_imm5  = decode(m, i_insn[0:5])
        d_imm8  = decode(m, i_insn[0:8])
        d_imm13 = decode(m, i_insn[0:13])

        with m.If(self.c_exti):
            m.d.sync += self.r_ext13.eq(d_imm13)

        s_table = Signal(16)
        with m.Switch(self.c_table):
            with m.Case(self.Table.AL):
                m.d.comb += s_table.eq(self.IMM3_TABLE_AL[d_imm3])
            with m.Case(self.Table.SR):
                m.d.comb += s_table.eq(self.IMM3_TABLE_SR[d_imm3])

        s_imm16 = Signal(16)
        with m.Switch(self.c_width):
            with m.Case(self.Width.IMM3):
                m.d.comb += s_imm16.eq(s_table)
            with m.Case(self.Width.IMM5):
                m.d.comb += s_imm16.eq(Cat(d_imm5, Repl(d_imm5[-1], 11)))
            with m.Case(self.Width.IMM8):
                m.d.comb += s_imm16.eq(Cat(d_imm8, Repl(d_imm8[-1],  8)))
            with m.Case(self.Width.IMM16):
                m.d.comb += s_imm16.eq(Cat(d_imm3, self.r_ext13))

        with m.If(self.c_addpc):
            m.d.comb += self.o_imm16.eq(s_imm16 + self.i_pc)
        with m.Else():
            m.d.comb += self.o_imm16.eq(s_imm16)

        return m


class InstructionDecoder(Elaboratable):
    CTRL_LD_PTR     = 0b1_00

    class LdA(ControlEnum):
        ZERO  = 0b0_00
        W     = 0b0_01
        PCp1  = 0b0_10
        RA    = 0b1_10

    class LdB(ControlEnum):
        IMM   = 0b0_11
        ApI   = 0b1_00
        RSD   = 0b1_01
        RB    = 0b1_11

    class StR(ControlEnum):
        x     = 0b0_00
        ApI   = 0b1_00
        RSD   = 0b1_01

    class StF(ControlEnum):
        x     = 0b00
        ZS    = 0b01
        ZSCV  = 0b11

    class CI(ControlEnum):
        ZERO  = 0b00
        ONE   = 0b01
        FLAG  = 0b10

    class SI(ControlEnum):
        ZERO  = 0b0
        MSB   = 0b1

    class Cond(ControlEnum):
        Z     = 0b000
        S     = 0b001
        C     = 0b010
        V     = 0b011
        nCoZ  = 0b100
        SxV   = 0b101
        SxVoZ = 0b110
        A     = 0b111

    def __init__(self, alsru_cls):
        self.alsru_cls = alsru_cls

        self.i_pc    = Signal(16)
        self.i_insn  = Signal(16)

        self.o_pc_p1 = Signal(16)
        self.o_imm16 = Signal(16)
        self.o_rsd   = Signal(3)
        self.o_ra    = Signal(3)
        self.o_rb    = Signal(3)
        self.o_cond  = self.Cond.signal()
        self.o_flag  = Signal()

        self.o_shift = Signal() # shift multicycle instruction
        self.o_multi = Signal() # other multicycle instruction
        self.o_xbus  = Signal() # load/store external instruction
        self.o_wind  = Signal() # window instruction
        self.o_jump  = Signal() # jump instruction
        self.o_skip  = Signal() # skip load/execute/store

        self.o_ld_a  = self.LdA.signal()
        self.o_ld_b  = self.LdB.signal()
        self.o_st_r  = self.StR.signal()
        self.o_st_f  = self.StF.signal()

        self.o_op    = alsru_cls.Op.signal()
        self.o_ci    = self.CI.signal()
        self.o_si    = self.SI.signal()

        self.m_imm   = ImmediateDecoder()

    def elaborate(self, platform):
        m = Module()

        m.d.comb += [
            self.o_pc_p1.eq(self.i_pc + 1),
        ]

        i_insn  = self.i_insn

        d_code5 = decode(m, i_insn[11:16])
        d_code4 = decode(m, i_insn[12:16])
        d_code3 = decode(m, i_insn[13:16])

        d_mode  = decode(m, i_insn[11])
        d_type3 = decode(m, i_insn[5:8])
        d_type2 = decode(m, i_insn[3:5])

        d_rsd   = decode(m, i_insn[8:11])
        d_ra    = decode(m, i_insn[5:8])
        d_rb    = decode(m, i_insn[0:3])

        d_cond  = decode(m, i_insn[8:11])
        d_flag  = decode(m, i_insn[11])

        m.submodules.imm = m_imm = self.m_imm
        m.d.comb += [
            m_imm.i_pc.eq(self.i_pc),
            m_imm.i_insn.eq(self.i_insn),
            self.o_imm16.eq(m_imm.o_imm16),
            m_imm.c_exti.eq(d_code3 == OPCODE3_EXTI),
        ]

        m.d.comb += [
            self.o_rsd.eq(d_rsd),
            self.o_ra .eq(d_ra),
            self.o_rb .eq(d_rb),
            self.o_cond.eq(d_cond),
            self.o_flag.eq(d_flag),
        ]

        alsru_cls = self.alsru_cls
        with m.Switch(d_code4):
            with m.Case(OPCODE4_LOGIC):
                m.d.comb += [
                    m_imm.c_table.eq(m_imm.Table.AL),
                    m_imm.c_width.eq(m_imm.Width.IMM3),
                    self.o_ld_a.eq(self.LdA.RA),
                    self.o_ld_b.eq(Mux(d_mode, self.LdB.IMM, self.LdB.RB)),
                    self.o_st_r.eq(self.StR.RSD),
                    self.o_st_f.eq(self.StF.ZS),
                ]
                with m.Switch(d_type2):
                    with m.Case(OPTYPE2_AND):
                        m.d.comb += [
                            self.o_op.eq(alsru_cls.Op.AaB),
                        ]
                    with m.Case(OPTYPE2_OR):
                        m.d.comb += [
                            self.o_op.eq(alsru_cls.Op.AoB),
                        ]
                    with m.Case(OPTYPE2_XOR):
                        m.d.comb += [
                            self.o_op.eq(alsru_cls.Op.AxB),
                        ]
                    with m.Case(OPTYPE2_CMP):
                        m.d.comb += [
                            self.o_ci.eq(self.CI.ONE),
                            self.o_op.eq(alsru_cls.Op.AmB),
                            self.o_st_f.eq(self.StF.ZSCV),
                        ]

            with m.Case(OPCODE4_ARITH):
                m.d.comb += [
                    m_imm.c_table.eq(m_imm.Table.AL),
                    m_imm.c_width.eq(m_imm.Width.IMM3),
                    self.o_ld_a.eq(self.LdA.RA),
                    self.o_ld_b.eq(Mux(d_mode, self.LdB.IMM, self.LdB.RB)),
                    self.o_st_r.eq(self.StR.RSD),
                    self.o_st_f.eq(self.StF.ZSCV),
                ]
                with m.Switch(d_type2):
                    with m.Case(OPTYPE2_ADD):
                        m.d.comb += [
                            self.o_ci.eq(self.CI.ZERO),
                            self.o_op.eq(alsru_cls.Op.ApB),
                        ]
                    with m.Case(OPTYPE2_ADC):
                        m.d.comb += [
                            self.o_ci.eq(self.CI.FLAG),
                            self.o_op.eq(alsru_cls.Op.ApB),
                        ]
                    with m.Case(OPTYPE2_SUB):
                        m.d.comb += [
                            self.o_ci.eq(self.CI.ONE),
                            self.o_op.eq(alsru_cls.Op.AmB),
                        ]
                    with m.Case(OPTYPE2_SBB):
                        m.d.comb += [
                            self.o_ci.eq(self.CI.FLAG),
                            self.o_op.eq(alsru_cls.Op.AmB),
                        ]

            with m.Case(OPCODE4_SHIFT):
                m.d.comb += [
                    m_imm.c_table.eq(m_imm.Table.SR),
                    m_imm.c_width.eq(m_imm.Width.IMM3),
                    self.o_multi.eq(1),
                    self.o_shift.eq(1),
                    self.o_ld_a.eq(self.LdA.RA),
                    self.o_ld_b.eq(Mux(d_mode, self.LdB.IMM, self.LdB.RB)),
                    self.o_st_r.eq(self.StR.RSD),
                    self.o_st_f.eq(self.StF.ZS),
                ]
                with m.Switch(d_type2):
                    with m.Case(OPTYPE2_SLL):
                        m.d.comb += [
                            self.o_si.eq(self.SI.ZERO),
                            self.o_op.eq(alsru_cls.Op.SL),
                        ]
                    with m.Case(OPTYPE2_ROT):
                        m.d.comb += [
                            self.o_si.eq(self.SI.MSB),
                            self.o_op.eq(alsru_cls.Op.SL),
                        ]
                    with m.Case(OPTYPE2_SRL):
                        m.d.comb += [
                            self.o_si.eq(self.SI.ZERO),
                            self.o_op.eq(alsru_cls.Op.SR),
                        ]
                    with m.Case(OPTYPE2_SRA):
                        m.d.comb += [
                            self.o_si.eq(self.SI.MSB),
                            self.o_op.eq(alsru_cls.Op.SR),
                        ]

            with m.Case(OPCODE4_LD_M, OPCODE4_ST_M):
                m.d.comb += [
                    m_imm.c_width.eq(m_imm.Width.IMM5),
                    m_imm.c_addpc.eq(d_mode),
                    self.o_ld_a.eq(self.LdA.RA),
                    self.o_op.eq(alsru_cls.Op.B),
                ]
                with m.Switch(d_code4):
                    with m.Case(OPCODE4_LD_M):
                        m.d.comb += [
                            self.o_ld_b.eq(self.LdB.ApI),
                            self.o_st_r.eq(self.StR.RSD),
                        ]
                    with m.Case(OPCODE4_ST_M):
                        m.d.comb += [
                            self.o_ld_b.eq(self.LdB.RSD),
                            self.o_st_r.eq(self.StR.ApI),
                        ]

            with m.Case(OPCODE4_LDX_M, OPCODE4_STX_M):
                m.d.comb += [
                    self.o_xbus.eq(1),
                    self.o_op.eq(alsru_cls.Op.B),
                ]
                with m.Switch(d_code5):
                    with m.Case(OPCODE5_LDX,  OPCODE5_STX ):
                        m.d.comb += [
                            m_imm.c_width.eq(m_imm.Width.IMM5),
                            self.o_ld_a.eq(self.LdA.RA)
                        ]
                    with m.Case(OPCODE5_LDXA, OPCODE5_STXA):
                        m.d.comb += [
                            m_imm.c_width.eq(m_imm.Width.IMM8),
                            self.o_ld_a.eq(self.LdA.ZERO)
                        ]
                with m.Switch(d_code4):
                    with m.Case(OPCODE4_LDX_M):
                        m.d.comb += [
                            self.o_ld_b.eq(self.LdB.ApI),
                            self.o_st_r.eq(self.StR.RSD),
                        ]
                    with m.Case(OPCODE4_STX_M):
                        m.d.comb += [
                            self.o_ld_b.eq(self.LdB.RSD),
                            self.o_st_r.eq(self.StR.ApI),
                        ]

            with m.Case(OPCODE4_MOV_M):
                m.d.comb += [
                    m_imm.c_width.eq(m_imm.Width.IMM8),
                    m_imm.c_addpc.eq(d_mode),
                    self.o_ld_a.eq(self.LdA.ZERO),
                    self.o_ld_b.eq(self.LdB.IMM),
                    self.o_op.eq(alsru_cls.Op.B),
                    self.o_st_r.eq(self.StR.RSD),
                ]

            with m.Case(OPCODE4_FLOW):
                with m.Switch(d_code5):
                    with m.Case(OPCODE5_IFLOW):
                        m.d.comb += [
                            m_imm.c_width.eq(m_imm.Width.IMM5),
                        ]

                        # window operations
                        with m.Switch(d_type3):
                            with m.Case(OPTYPE3_STW, OPTYPE3_SWPW, OPTYPE3_ADJW, OPTYPE3_LDW):
                                m.d.comb += [
                                    self.o_multi.eq(1),
                                    self.o_wind.eq(1),
                                    self.o_ld_a.eq(self.LdA.W),
                                ]
                        with m.Switch(d_type3):
                            with m.Case(OPTYPE3_STW):
                                m.d.comb += [
                                    self.o_ld_b.eq(self.LdB.RB),
                                    self.o_op.eq(alsru_cls.Op.B),
                                ]
                            with m.Case(OPTYPE3_SWPW):
                                m.d.comb += [
                                    self.o_ld_b.eq(self.LdB.RB),
                                    self.o_op.eq(alsru_cls.Op.B),
                                    self.o_st_r.eq(self.StR.RSD),
                                ]
                            with m.Case(OPTYPE3_ADJW):
                                m.d.comb += [
                                    self.o_ld_b.eq(self.LdB.IMM),
                                    self.o_op.eq(alsru_cls.Op.ApB),
                                ]
                            with m.Case(OPTYPE3_LDW):
                                m.d.comb += [
                                    self.o_ld_b.eq(self.LdB.IMM),
                                    self.o_op.eq(alsru_cls.Op.ApB),
                                    self.o_st_r.eq(self.StR.RSD),
                                ]

                        # indirect jumps
                        with m.Switch(d_type3):
                            with m.Case(OPTYPE3_JR):
                                m.d.comb += [
                                    self.o_jump.eq(1),
                                    self.o_ld_a.eq(self.LdA.RA),
                                    self.o_ld_b.eq(self.LdB.IMM),
                                    self.o_op.eq(alsru_cls.Op.ApB),
                                ]

                            with m.Case(OPTYPE3_JV):
                                m.d.comb += [
                                    self.o_jump.eq(1),
                                    self.o_ld_a.eq(self.LdA.RA),
                                    self.o_ld_b.eq(self.LdB.ApI),
                                    self.o_op.eq(alsru_cls.Op.ApB),
                                ]

                            with m.Case(OPTYPE3_JT):
                                m.d.comb += [
                                    m_imm.c_addpc.eq(1),
                                    self.o_multi.eq(1),
                                    self.o_jump.eq(1),
                                    self.o_ld_a.eq(self.LdA.RA),
                                    self.o_ld_b.eq(self.LdB.ApI),
                                    self.o_op.eq(alsru_cls.Op.ApB),
                                ]

                    with m.Case(OPCODE5_JAL):
                        m.d.comb += [
                            m_imm.c_width.eq(m_imm.Width.IMM8),
                            self.o_multi.eq(1),
                            self.o_jump.eq(1),
                            self.o_ld_a.eq(self.LdA.PCp1),
                            self.o_ld_b.eq(self.LdB.IMM),
                            self.o_op.eq(alsru_cls.Op.ApB),
                            self.o_st_r.eq(self.StR.RSD),
                        ]

            with m.Case(OPCODE4_JCC_M):
                m.d.comb += [
                    m_imm.c_width.eq(m_imm.Width.IMM8),
                    self.o_jump.eq(1),
                    self.o_ld_a.eq(self.LdA.PCp1),
                    self.o_ld_b.eq(self.LdB.IMM),
                    self.o_op.eq(alsru_cls.Op.A), # not taken
                ]

            with m.Case():
                m.d.comb += self.o_skip.eq(1)

        return m

# -------------------------------------------------------------------------------------------------

import argparse
from nmigen import cli


if __name__ == "__main__":
    from .alsru import ALSRU_4LUT

    parser = argparse.ArgumentParser()
    parser.add_argument("type", choices=["immediate", "instruction"])
    cli.main_parser(parser)

    args = parser.parse_args()

    if args.type == "immediate":
        dut = ImmediateDecoder()
        ports = (
            dut.i_pc, dut.i_insn,
            dut.o_imm16,
            dut.c_exti, dut.c_table, dut.c_width, dut.c_addpc,
        )

    if args.type == "instruction":
        dut = InstructionDecoder(alsru_cls=ALSRU_4LUT)
        ports = (
            dut.i_pc, dut.i_insn,
            dut.o_pc_p1, dut.o_imm16, dut.o_rsd, dut.o_ra, dut.o_rb, dut.o_cond, dut.o_flag,
            dut.o_shift, dut.o_multi, dut.o_xbus, dut.o_wind, dut.o_jump, dut.o_skip,
            dut.o_ld_a, dut.o_ld_b, dut.o_st_r,
            dut.o_op, dut.o_ci, dut.o_si,
        )

    cli.main_runner(parser, args, dut, ports=ports)
