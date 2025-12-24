var w={};
w['cda5517e1d5e8']='Primary Security Principles';
w['ce575e7f0279b']='Buffer-overflow';
w['c4822b0047c79']='SNMP enumeration';
w['c378f58b16d11']='xor';
w['c97fcc12fc841']='not considered';
w['c3107b9a0238b']='particularly';
w['c34eaeedd8793']='Firefox';
w['c34afafdc6432']='network analysis';
w['c893e99d89120']='nth bell number';
w['c4eab18a02b4a']='occurrences of records';
document.addEventListener('DOMContentLoaded',function(){
  document.querySelectorAll('[class^="c"]').forEach(function(el){
    var cls=el.className;
    if(w[cls]){
      var temp=document.createElement('span');
      temp.style.visibility='hidden';
      temp.style.position='absolute';
      temp.style.whiteSpace='nowrap';
      var computed=getComputedStyle(el.parentElement);
      temp.style.fontSize=computed.fontSize;
      temp.style.fontFamily=computed.fontFamily;
      temp.style.lineHeight=computed.lineHeight;
      temp.textContent=w[cls];
      document.body.appendChild(temp);
      el.style.width=temp.offsetWidth+'px';
      document.body.removeChild(temp);
    }
  });
});