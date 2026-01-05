var w={};
w['c3bf6d873d216']='twice its rest energy';
w['cbc886a1b687b']='linear momentum and wavelength';
w['cb433910e2833']='time required for one revolution is';
w['cb32d95e5d641']='The angular magnification of the telescope is';
w['c78dd51a405d6']='voltage across the resistor is doubled';
w['cc179472a2e6b']='temperature';
w['c4cde8fadd735']='microwaves';
w['c1d7ac173e386']='4.0';
w['cb75d051933fd']='sign';
w['cea27b927dd31']='electron';
w['c78274421b0a9']='doubly ionized lithium (Li++)';
w['c89fbeb902f98']='at 1/2 c';
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