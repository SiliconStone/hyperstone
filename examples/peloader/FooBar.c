//
// Created by Itay Sharon on 03/05/2024.
//

#include "FooBar.h"

static volatile void * g_ADDRESS = (void *)0xdeaddef0;
static volatile void ** g_addr2 = &g_ADDRESS;

void DLLEXPORT FooBar()
{
    int ** x = g_addr2;

    **x = 69;
}