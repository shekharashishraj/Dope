var w={};
w['c2b13316a7b98']='20 miles per hour';
w['cfed4d732a1f8']='nearest thousand';
w['c853c8d3ed990']='F(t) = (t^2 + 1, 2^t)';
w['c8a9795dc65f9']='shortest';
w['c2e7912e33d9b']='3 hours';
w['c5f7f05da9839']='45';
w['cd4dea30ab998']='Forty-nine';
w['ca5ea4311943c']='1:4';
w['c58e852d1759e']='23';
w['c28f28066f535']='not in the domain';
w['c204b0e91c5a2']='factors that can influence';
w['cb2c98053ef95']='maximum possible value of the quotient';
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