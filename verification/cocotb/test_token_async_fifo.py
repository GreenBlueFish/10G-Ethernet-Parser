import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer
import random
from collections import deque

async def rst_all(dut):
	dut.w_en.value = 1
	dut.r_en.value = 1
	dut.rrst_n.value = 1
	dut.wrst_n.value = 1
	await Timer(1, unit="ns")
	dut.rrst_n.value = 0
	dut.wrst_n.value = 0
	await Timer(1, unit="ns")
	dut.rrst_n.value = 1
	dut.wrst_n.value = 1
	dut.w_en.value = 0
	dut.r_en.value = 0
	await Timer(1, unit="ns")

async def one_clk_cycle(dut, cycles: int = 1):
	await ClockCycles(dut.wclk, cycles)
	await ClockCycles(dut.rclk, cycles)

async def write_value(dut, data: int):
	dut.w_en.value = 1
	dut.wrst_n.value = 1
	dut.wdata_in.value = data
	await Timer(1, unit="ns")
	await ClockCycles(dut.wclk, 1)

	dut.w_en.value = 0
	await Timer(1, unit="ns")

async def read_value(dut):
	dut.r_en.value = 1
	dut.rrst_n.value = 1
	await Timer(1, unit="ns")
	await ClockCycles(dut.rclk, 1)
	dout = dut.rdata_out.value

	dut.r_en.value = 0
	await Timer(1, unit="ns")

	return dout

async def print_title(dut, title: str = ""):
	dut._log.info(f"-----------------------")
	if title == "":
		dut._log.info(f"-----------------------")
	else:
		dut._log.info(f"{title}")
	dut._log.info(f"-----------------------")

async def print_writes_ios(dut):
	dut._log.info(f"wclk:		{dut.wclk.value}")
	dut._log.info(f"wrst_n:		{dut.wrst_n.value}")
	dut._log.info(f"w_en:		{dut.w_en.value}")
	dut._log.info(f"wdata_in:	{dut.wdata_in.value}")
	dut._log.info(f"wfull:  	{dut.wfull.value}")

async def print_read_ios(dut):
	dut._log.info(f"rclk:		{dut.rclk.value}")
	dut._log.info(f"rrst_n:		{dut.rrst_n.value}")
	dut._log.info(f"r_en:		{dut.r_en.value}")
	dut._log.info(f"rdata_out:	{dut.rdata_out.value}")
	dut._log.info(f"rempty:		{dut.rempty.value}")

async def print_dut_info(dut):
	await print_writes_ios(dut)
	await print_read_ios(dut)
	#await print_rings(dut)
	#await print_FIFO(dut)

FIFO_DEPTH = 8

@cocotb.test()
async def test_token_async_fifo(dut):
	# Set the clock period to 100 ns for both clocks (10 MHz)
	w_clock = Clock(dut.wclk, 100, unit="ns")
	cocotb.start_soon(w_clock.start())

	r_clock = Clock(dut.rclk, 100, unit="ns")
	cocotb.start_soon(r_clock.start())

	await print_title(dut, "Resetting")
	await rst_all(dut)
	await print_dut_info(dut)

	await print_title(dut, "Testing read write")

	''' Good loop version '''
	#python fifo to see if verilog fifo works
	temp_fifo = deque()

	#test loop variables
	for run in range(100000):
		n = random.randint(1,FIFO_DEPTH+2)
		dut._log.info(f"rand n: {n}")
		for i in range(n):
			#if the dut is full do not write anything more to the fifo
			if(dut.wfull.value == 0):
				rand_int_32 = random.randint(0, (2**32)-1)
				temp_fifo.append(rand_int_32)
				await write_value(dut, rand_int_32)
			else:
				dut._log.info(f"w full")
				break

		l = random.randint(1, FIFO_DEPTH+2)
		dut._log.info(f"rand l: {l}")
		for i in range(l):
			#if the dut is empty do not read anything more to the fifo
			if(dut.rempty.value == 0):
				my_answer = await read_value(dut)
				if str(my_answer).lower() == 'z' * len(str(my_answer)):
					dut._log.info(f"My answer is high-z")
					continue
				correct_answer = temp_fifo.popleft()
				assert int(my_answer) == correct_answer, f"my_answer != correct_answer"
			else:
				dut._log.info(f"r empty")
				break

		dut._log.info(f"End of round {run}")
