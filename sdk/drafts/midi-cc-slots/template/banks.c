/* SPDX-License-Identifier: MIT
 * Checked, length-preserving channel-sector updates. No stock serializer.
 */
#include "template.h"
#include "banks.h"
static uint32_t nibble[16];
struct bank_info {uint32_t hash;unsigned sum,stored;uint8_t channels[64];};
static uint32_t read_be(const uint8_t*p){return (uint32_t)p[0]<<24|(uint32_t)p[1]<<16|(uint32_t)p[2]<<8|p[3];}
static void write_be(uint8_t*p,uint32_t v){p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static unsigned cell(unsigned i){return 0x8eed6u+(i/8)*0x18bbu+9+0x4e2u+(i%8)*36u;}
static void bank_path(char*name,const char*folder,unsigned bank,unsigned saved){
    unsigned n=0;while(folder[n]){name[n]=folder[n];++n;}if(n&&name[n-1]!='/')name[n++]='/';
    const char*p="bank";while(*p)name[n++]=*p++;
    name[n++]=(char)('0'+(bank+1)/10);name[n++]=(char)('0'+(bank+1)%10);
    p=saved?".strd":".work";while(*p)name[n++]=*p++;name[n]=0;
}
static int inspect_bank(const char*name,struct bank_info*info){
    struct mt_bank_file f;if(!mt_bank_open(&f,name,0))return 0;
    unsigned valid=mt_bank_size(&f)==636113;
    info->sum=info->stored=0;uint32_t hash=~0u;
    for(unsigned at=0;valid&&at<636113;){
        unsigned n=636113-at;if(n>4096)n=4096;
        if(!mt_bank_read(&f,mt_work,n)){valid=0;break;}
        if(!at&&!(mt_work[0]=='F'&&mt_work[1]=='O'&&mt_work[2]=='R'&&mt_work[3]=='M'&&mt_work[12]=='B'&&mt_work[13]=='A'&&mt_work[14]=='N'&&mt_work[15]=='K'))valid=0;
        for(unsigned i=0;i<n;i++){
            unsigned pos=at+i;if(pos>=16&&pos<636111)info->sum+=mt_work[i];
            if(pos==636111)info->stored=(unsigned)mt_work[i]<<8;if(pos==636112)info->stored|=mt_work[i];
        }
        for(unsigned i=0;i<64;i++){
            unsigned pos=cell(i);
            if(pos>=at&&pos<at+n){volatile unsigned relative=pos-at;info->channels[i]=mt_work[relative];mt_work[relative]=0;}
        }
        for(unsigned i=0;i<n;i++){
            unsigned pos=at+i;uint8_t v=pos>=636111?0:mt_work[i];
            hash^=v;hash=(hash>>4)^nibble[hash&15];hash=(hash>>4)^nibble[hash&15];
        }
        at+=n;
    }
    info->hash=~hash;
    return mt_bank_close(&f)&&valid;
}
static void hash_init(void){if(nibble[1])return;for(unsigned i=0;i<16;i++){uint32_t c=i;for(unsigned b=0;b<4;b++)c=(c>>1)^(0xedb88320u&(0u-(c&1u)));nibble[i]=c;}}
int mt_preflight(const uint8_t values[1024],uint8_t fingerprints[128]){
    hash_init();char folder[260],name[300];if(!mt_stopped()||!mm_profile_directory(folder,260))return 0;
    for(unsigned b=0;b<16;b++){
        uint32_t first=0;
        for(unsigned saved=0;saved<2;saved++){
            struct bank_info info;bank_path(name,folder,b,saved);
            if(!inspect_bank(name,&info)||(info.sum&65535)!=info.stored)return 0;
            for(unsigned i=0;i<64;i++)if(info.channels[i]!=values[b*64+i])return 0;
            if(saved&&first!=info.hash)return 0;first=info.hash;
            write_be(fingerprints+(b*2+saved)*4,info.hash);
        }
    }
    return 1;
}
static int restore_peer(const char*good,const char*bad){
    struct mt_bank_file input,output;if(!mt_bank_open(&input,good,0))return 0;
    if(!mt_bank_open(&output,bad,1)){mt_bank_close(&input);return 0;}
    output.word[4]=636113;unsigned valid=1;
    for(unsigned at=0;valid&&at<636113;){
        unsigned n=636113-at;if(n>4096)n=4096;
        if(!mt_bank_read(&input,mt_work,n)){valid=0;break;}
        unsigned padded=(n+511)&~511u;for(unsigned i=n;i<padded;i++)mt_work[i]=0;
        if(!mt_bank_write(&output,mt_work,padded))valid=0;at+=n;
    }
    int out_ok=mt_bank_close(&output),in_ok=mt_bank_close(&input);return valid&&out_ok&&in_ok;
}
static int patch_bank(const char*name,const uint8_t values[64],const struct bank_info*before){
    unsigned sum=before->sum;
    for(unsigned i=0;i<64;i++)sum=sum-before->channels[i]+values[i];sum&=65535;
    struct mt_bank_file input,output;if(!mt_bank_open(&input,name,0))return 0;
    if(!mt_bank_open(&output,name,1)){mt_bank_close(&input);return 0;}output.word[4]=636113;
    unsigned sectors[65],count=0,previous=~0u;
    for(unsigned i=0;i<64;i++){unsigned s=cell(i)&~511u;if(s!=previous)sectors[count++]=s;previous=s;}
    sectors[count++]=636111u&~511u;unsigned valid=1;
    for(unsigned s=0;valid&&s<count;s++){
        unsigned at=sectors[s],n=636113-at;if(n>512)n=512;
        if(!mt_bank_seek(&input,at)||!mt_bank_read(&input,mt_work,n)){valid=0;break;}
        for(unsigned i=n;i<512;i++)mt_work[i]=0;
        for(unsigned i=0;i<64;i++){unsigned pos=cell(i);if(pos>=at&&pos<at+512){volatile unsigned relative=pos-at;mt_work[relative]=values[i];}}
        if(at==(636111u&~511u)){mt_work[636111u&511u]=(uint8_t)(sum>>8);mt_work[636112u&511u]=(uint8_t)sum;}
        if(!mt_bank_seek(&output,at)||!mt_bank_write(&output,mt_work,512))valid=0;
        output.word[4]=636113;
    }
    output.word[3]=0;output.word[4]=636113;
    int out_ok=mt_bank_close(&output),in_ok=mt_bank_close(&input);return valid&&out_ok&&in_ok;
}
int mt_persist(const uint8_t values[1024],const uint8_t fingerprints[128]){
    hash_init();char folder[260],name[2][300];if(!mt_stopped()||!mm_profile_directory(folder,260))return 0;
    for(unsigned b=0;b<16;b++){
        struct bank_info info[2];unsigned valid[2];
        for(unsigned s=0;s<2;s++){bank_path(name[s],folder,b,s);valid[s]=inspect_bank(name[s],&info[s])&&info[s].hash==read_be(fingerprints+(b*2+s)*4);}
        if(!valid[0]&&!valid[1])return 0;
        for(unsigned s=0;s<2;s++)if(!valid[s]){
            if(read_be(fingerprints+b*8)!=read_be(fingerprints+b*8+4)||!restore_peer(name[s^1],name[s])||!inspect_bank(name[s],&info[s])||info[s].hash!=read_be(fingerprints+(b*2+s)*4))return 0;
        }
        for(unsigned s=0;s<2;s++){
            if(!patch_bank(name[s],values+b*64,&info[s])||!inspect_bank(name[s],&info[s])||info[s].hash!=read_be(fingerprints+(b*2+s)*4)||(info[s].sum&65535)!=info[s].stored)return 0;
            for(unsigned i=0;i<64;i++)if(info[s].channels[i]!=values[b*64+i])return 0;
        }
    }
    return 1;
}
