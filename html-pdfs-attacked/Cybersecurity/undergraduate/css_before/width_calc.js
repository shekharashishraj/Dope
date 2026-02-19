var w={};
w['cc3aaf5047956']='verify';
w['ca6a811b8b16a']='network intrusion detection and real-time traffic analysis';
w['c73367ae1a87f']='digest';
w['c19739717cf70']='when the STP solver times out on a constraint query for a particular path';
w['ccdb3cff41d3e']='perfect secrecy';
w['caf2b5f2b113e']='cannot';
w['c4d09fcdb4cfb']='56';
w['c60cfcec7dcdf']='particularly vulnerable to';
w['c9a4b6c9eb458']='EtterPeak';
w['c3935c2a9d7f5']='Access Control';
w['c06aae1e6d874']='zero or one';
w['c2d9b07d97ac7']='starts and ends';
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