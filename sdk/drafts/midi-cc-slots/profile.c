/* SPDX-License-Identifier: MIT
 * Original project-wide MIDI profile. No stock file-format bytes are stored.
 * Two project-local checkpoints preserve the last verified generation.
 */
#include "profile.h"
struct profile {
    uint8_t defaults[8], channels[64][8], initialized[8];
};
static struct profile state;
static char directory[260];
static uint32_t generation;
static unsigned loaded, dirty, pending_wake, redraw, status;
static uint8_t selected = 255, peer;
static unsigned ticks;
static uint32_t revision;
static void copy(void *to,const void *from,unsigned n) {
    uint8_t *d=to;const uint8_t *s=from;while(n--)*d++=*s++;
}
static int equal(const void *a,const void *b,unsigned n) {
    const uint8_t *x=a,*y=b;while(n--)if(*x++!=*y++)return 0;return 1;
}
static uint32_t get32(const uint8_t *p) {
    return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];
}
static void put32(uint8_t *p,uint32_t v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static uint32_t crc(const uint8_t *p) {
    uint32_t c=~0u;
    for(unsigned i=0;i<MM_PROFILE_BYTES-4;i++) {
        c^=p[i];for(unsigned b=0;b<8;b++)c=(c>>1)^(0xedb88320u&(0u-(c&1u)));
    }
    return ~c;
}
static void announce(unsigned now) {if(status!=now)status=now,redraw=1;}
static void reset(void) {
    uint8_t *p=(uint8_t *)&state;for(unsigned i=0;i<sizeof state;i++)p[i]=0;
    for(unsigned t=0;t<8;t++)for(unsigned c=0;c<16;c++)names_store[t][c]=0;
    generation=dirty=0;selected=255;peer=0;loaded=1;
}
static int path(char *out,unsigned slot) {
    unsigned n=0;
    while(directory[n]) {if(n>240)return 0;out[n]=directory[n];++n;}
    if(!n)return 0;
    if(out[n-1]!='/')out[n++]='/';
    const char *suffix=slot?"MIDI2_1.DAT":"MIDI2_0.DAT";
    while(*suffix)out[n++]=*suffix++;
    out[n]=0;return 1;
}
static int owned(const uint8_t *p) {return get32(p)==0x4d4d3250u&&get32(p+4)==1;}
static int valid(const uint8_t *p) {
    if(!owned(p)||get32(p+MM_PROFILE_BYTES-4)!=crc(p))return 0;
    for(unsigned t=0;t<8;t++) {
        unsigned end=0;
        for(unsigned c=0;c<16;c++) {
            unsigned v=p[16+16*t+c];
            if(!v)end=1;
            else if(end||c>=10||v<32||v>254)return 0;
        }
    }
    for(unsigned i=0;i<520;i++)if(p[144+i]>16)return 0;
    return 1;
}
static void unpack(const uint8_t *p) {
    copy(names_store,p+16,128);copy(state.defaults,p+144,8);
    copy(state.channels,p+152,512);copy(state.initialized,p+664,8);
    generation=get32(p+8);
}
static void pack(uint8_t *p,uint32_t gen) {
    for(unsigned i=0;i<MM_PROFILE_BYTES;i++)p[i]=0;
    put32(p,0x4d4d3250u);put32(p+4,1);put32(p+8,gen);
    for(unsigned t=0;t<8;t++)for(unsigned c=0;c<10&&names_store[t][c];c++)p[16+t*16+c]=(uint8_t)names_store[t][c];
    copy(p+144,state.defaults,8);
    copy(p+152,state.channels,512);copy(p+664,state.initialized,8);
    put32(p+MM_PROFILE_BYTES-4,crc(p));
}
static void load(void) {
    uint8_t data[MM_PROFILE_BYTES];char file[260];
    reset();unsigned found=0,damaged=0;
    for(unsigned slot=0;slot<2;slot++)if(path(file,slot)) {
        int result=mm_profile_file(0,file,data,sizeof data);
        if(result==1&&valid(data)) {
            uint32_t g=get32(data+8);
            if(!found||(int32_t)(g-generation)>0)unpack(data),peer=slot^1u,found=1;
        } else if(result!=0)damaged=1;
    }
    announce(found?1:damaged?4:0);
}
static void save(void) {
    uint8_t data[MM_PROFILE_BYTES];char file[260];
    if(!path(file,peer)){announce(3);return;}
    /* Refuse a foreign file even when a stale peer can otherwise be replaced. */
    int exists=mm_profile_file(0,file,data,sizeof data);
    if(exists<0||(exists==1&&!owned(data))){announce(3);return;}
    uint32_t next=generation+1;
    uint32_t snapshot=revision;
    pack(data,next);
    if(snapshot!=revision)return;
    if(mm_profile_file(1,file,data,sizeof data)!=1||mm_profile_file(0,file,data,sizeof data)!=1||!valid(data)||get32(data+8)!=next) {announce(3);return;}
    generation=next;peer^=1u;
    if(snapshot==revision)dirty=0,announce(2);
}
void mm_profile_changed(void) {++revision;dirty=1;announce(5);}
unsigned mm_profile_ready(void) {return loaded;}
unsigned mm_profile_status(void) {return status;}
void mm_profile_tick(void *api) {
    (void)api;
    if(redraw){redraw=0;mm_profile_redraw(status);}
    if(++ticks<60&&loaded&&!dirty)return;
    ticks=0;
    if(!pending_wake){pending_wake=1;if(!mm_profile_wake())pending_wake=0;}
}
void mm_profile_service(void) {
    pending_wake=0;
    if(!mm_profile_gate())return;
    char current[260];
    if(!mm_profile_directory(current,sizeof current))return;
    unsigned n=0;while(current[n]&&n<sizeof current-1)++n;
    if(current[n]||!n)return;
    if(!loaded||!equal(current,directory,n+1)) {
        copy(directory,current,n+1);load();
        /* Project switching must never carry the old project's edit into another. */
        ++revision;
    }
    unsigned bank,part;uint8_t channels[8];
    mm_profile_context(&bank,&part,channels);
    if(bank>15||part>3)return;
    unsigned at=bank*4+part,bit=1u<<(at&7u),byte=at>>3;
    if(at!=selected) {
        if(state.initialized[byte]&bit) {
            mm_profile_apply(state.channels[at]);
            copy(channels,state.channels[at],8);
        } else {
            for(unsigned t=0;t<8;t++)if(bank&&channels[t]==0)channels[t]=state.defaults[t];
            copy(state.channels[at],channels,8);state.initialized[byte]|=(uint8_t)bit;
            mm_profile_apply(channels);dirty=1;
        }
        selected=(uint8_t)at;redraw=1;
    } else if(!equal(channels,state.channels[at],8)) {
        copy(state.channels[at],channels,8);dirty=1;
    }
    /* Bank A's first Part is the initial project template; later Parts/banks
     * keep their own channel profile, including explicit OFF overrides. */
    if(!at&&!equal(state.defaults,channels,8)) {copy(state.defaults,channels,8);dirty=1;}
    if(dirty)save();
}
