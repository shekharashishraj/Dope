var w={};
w['cc6aea7e18baf']='net primary productivity is important because it represents the';
w['ccd7409e72d88']='being digested';
w['c9dc72a76a8de']='genetic variation';
w['c0c091d89642a']='propose';
w['cf1f833e26028']='determine whether or not a given population is in genetic equilibrium';
w['cc2f182a3181a']='destroyed';
w['cf27e375e154f']='effectively';
w['c141920295d90']='do not contain an inactivated X chromosome';
w['c02d35ab8c1a9']='not';
w['ca6e5fcc6b5e4']='sucrose';
w['cb3ed3c1b08fb']='Carboniferous Period';
w['cdbfd21e93353']='higher plants';
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