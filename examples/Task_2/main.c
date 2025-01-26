/*
 * Copyright (C) 2014 Freie Universität Berlin
 *
 * This file is subject to the terms and conditions of the GNU Lesser
 * General Public License v2.1. See the file LICENSE in the top level
 * directory for more details.
 */

/**
 * @ingroup     examples
 * @{
 *
 * @file
 * @brief       Hello World application
 *
 * @author      Kaspar Schleiser <kaspar@schleiser.de>
 * @author      Ludwig Knüpfer <ludwig.knuepfer@fu-berlin.de>
 *
 * @}
 */

#include <stdio.h>
#include <thread.h>
#include <xtimer.h>
#include <shell.h> 
#include <stdlib.h>


// 定时器线程堆栈大小
#define TIMER_THREAD_STACKSIZE (THREAD_STACKSIZE_MAIN)
static int send_interval_sec = 5;  // 5秒

// 定时器线程堆栈
static char timer_thread_stack[TIMER_THREAD_STACKSIZE];


static int cmd_set_interval(int argc, char **argv) {
    fflush(stdin);
    
    int par;
    if (argc != 2) {  // 参数检查，要求传入一个整数作为新的时间间隔
        printf("Usage: time <seconds>\n");
        return 0;
    }

    // 将输入的参数（字符串）转换为整数
    par = atoi(argv[1]); 
    if (par <= 0) {  // 输入必须是一个正整数
        printf("Error: must be positive\n");
        return 0;
    }

    // 输出更新后的间隔时间
    send_interval_sec = par;
    printf("Send interval updated to %d seconds\n", send_interval_sec);
    return 0;
}

static const shell_command_t commands[] = {
    { "time", "in seconds", cmd_set_interval },
    { NULL, NULL, NULL }
};


// 定时器线程函数
void *timer_thread(void *arg) {
    (void)arg;
    while (1) {
        xtimer_sleep(send_interval_sec); // 等待指定间隔时间

        
        puts("hello, world");
    }
    return NULL;
}


int main(void)
{
    puts("Hello World! start up");
    printf("You are running RIOT on a(n) %s board.\n", RIOT_BOARD);
    printf("This board features a(n) %s CPU.\n", RIOT_CPU);

    // 启动定时器线程
    thread_create(timer_thread_stack, sizeof(timer_thread_stack),
                  THREAD_PRIORITY_MAIN - 1, 0, timer_thread, NULL, "timer_thread");

    // 初始化并启动 Shell
    char line_buf[SHELL_DEFAULT_BUFSIZE];

    shell_run(commands, line_buf, SHELL_DEFAULT_BUFSIZE);
    
    return 0;
}
