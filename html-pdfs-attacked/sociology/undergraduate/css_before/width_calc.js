var w={};
w['cdbe69c001d7d']='disadvantaged pupils at school because';
w['c55fd1116e522']='a system of interdependent and coordinated parts';
w['c930b36e61736']='not a consequence';
w['c7a1a0a693958']='knowledge is \'value-relevant\'';
w['c4ece5d88660b']='disengagement';
w['cd226614f12f1']='move freely';
w['c921a9f7ec5b3']='industrial capitalism';
w['c7a746133d584']='is exploited';
w['c1edcb4672a49']='current research findings on gender roles';
w['c7cb7e3206d31']='functionalist perspective';
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