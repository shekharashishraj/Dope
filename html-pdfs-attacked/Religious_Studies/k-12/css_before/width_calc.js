var w={};
w['c66a52dda6076']='anthropomorphic view of the divine';
w['c1f9a48256db0']='ajiva';
w['c08484a13d256']='Arhats';
w['c995ccd19fb9d']='How many times a day';
w['c77965e07bc8a']='shifted from cosmology to which of the following issues';
w['ce3c7a45f7848']='at the age of 30';
w['ccb3fece885c6']='argued against Pelagius';
w['c5f87727b165d']='Moses';
w['c2eacc76f0dcc']='Reformed';
w['c459642ff2de4']='Sunni';
w['c52ce0d77acc4']='mappo';
w['c25082f56d0d8']='Daoist concept of wuwei';
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