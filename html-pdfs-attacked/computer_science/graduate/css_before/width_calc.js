var w={};
w['cc2a208e527ad']='central node';
w['cb1b0a7af970a']='facilitate running attacker-injected code';
w['cacd954d6aaa5']='paths covering every line of code';
w['ca93f1ee93718']='Local caching of files is common in distributed file systems, but it has the disadvantage that';
w['c9bbd7a1f66cc']='digital signature needs a';
w['ca051c34d3ca8']='both confidentiality and integrity';
w['c3c9dfd4b85a1']='10000001';
w['ca7786c5d0aef']='without any hidden components';
w['cfe1785dad55e']='even number of zeros';
w['c55b3cdb51b6b']='O((log N)^2)';
w['c9e3c66379954']='nth digit';
w['c4f3690c281b6']='group the 1 st elements';
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