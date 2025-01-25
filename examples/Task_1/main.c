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


//Task 1
int main(void)
{
    puts("hello world");
    return 0;
}









/*
//Task 2
// 定时器线程堆栈大小
#define TIMER_THREAD_STACKSIZE (THREAD_STACKSIZE_MAIN)
static int send_interval_sec = 5;  // 5秒

// 定时器线程堆栈
static char timer_thread_stack[TIMER_THREAD_STACKSIZE];


static int cmd_set_interval(int argc, char **argv) {
    int par;
    if (argc != 2) {  // 参数检查，要求传入一个整数作为新的时间间隔
        printf("Usage: set_interval <seconds>\n");
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
    { "timeduration", "in seconds", cmd_set_interval },
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

*/








/*
//Task 3
// 定时器线程堆栈大小
#define TIMER_THREAD_STACKSIZE (THREAD_STACKSIZE_MAIN)
static int send_interval_sec = 10;  // 5秒

// Define message queues for inter-process communication
static msg_t msg_queue_1[8];
static msg_t msg_queue_2[8];
static msg_t msg_1;          
static msg_t msg_2; 

// 定时器线程堆栈
static char timer_thread_stack[TIMER_THREAD_STACKSIZE];
static char trigger_thread_stack[TIMER_THREAD_STACKSIZE];

// //flag
// static int triggered = 0;

// 目标进程 PID
static kernel_pid_t pid_process_1 = KERNEL_PID_UNDEF;


// The first process
void *process_1(void *arg) {
    (void)arg;
    int first_run = 1; // Flag to differentiate the first print

    // Get the process ID of process_1
    pid_process_1 = thread_getpid();

    while (1) {
        // Wait for a message to trigger the process
        msg_receive(&msg_1);

        // Based on the flag, print the appropriate message
        if (first_run) {
            printf("hello, world\n");
            first_run = 0;  // Only print this once
        } else {
            printf("hello again, world\n");
        }
    }

    return NULL;
}

// Shell command to restart process_1
static int cmd_restart_process_1(int argc, char **argv) {
    (void)argc;
    (void)argv;

    // Exit the current process if it is running
    if (pid_process_1 != KERNEL_PID_UNDEF) {
        thread_kill_zombie(pid_process_1);  // Exit the current process
        printf("Process 1 stopped\n");
    }

    // Restart process_1
    pid_process_1 = thread_create(timer_thread_stack, sizeof(timer_thread_stack),
                  THREAD_PRIORITY_MAIN - 1, 0, process_1, NULL, "process_1");
    printf("Process 1 restarted\n");

    return 0;
}

// The second process (Trigger process)
void *process_2(void *arg) {
    (void)arg;

    while (1) {
        // Trigger process_1 every `send_interval_sec` seconds
        xtimer_sleep(send_interval_sec);
        
        // Send a message to process_1
        msg_send(&msg_2, pid_process_1);
        printf("Process 2\n");
    }

    return NULL;
}


static int cmd_set_interval(int argc, char **argv) {
    int par;
    if (argc != 2) {  // 参数检查，要求传入一个整数作为新的时间间隔
        printf("Usage: set_interval <seconds>\n");
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

static int cmd_trigger_hello(int argc, char **argv) {
    (void)argc;
    (void)argv;

    // Send a message to process_1
    msg_send(&msg_2, pid_process_1);
    printf("Manual Trigger\n");

    return 0;
}

static const shell_command_t commands[] = {
    { "restart", "Restart process 1", cmd_restart_process_1 },
    { "time", "Set send interval in seconds", cmd_set_interval },
    { "trigger", "manual Trigger", cmd_trigger_hello },
    { NULL, NULL, NULL }
};


int main(void)
{
    puts("Start up");

    // Initialize the message queues
    msg_init_queue(msg_queue_1, 8);
    msg_init_queue(msg_queue_2, 8);

    // 启动定时器线程
    // Create the threads for both processes
    thread_create(timer_thread_stack, sizeof(timer_thread_stack),
                  THREAD_PRIORITY_MAIN - 1, 0, process_1, NULL, "process_1");
    thread_create(trigger_thread_stack, sizeof(trigger_thread_stack),
                  THREAD_PRIORITY_MAIN - 1, 0, process_2, NULL, "process_2");

    // 初始化并启动 Shell
    char line_buf[SHELL_DEFAULT_BUFSIZE];
    shell_run(commands, line_buf, SHELL_DEFAULT_BUFSIZE);
    
    return 0;
}


*/