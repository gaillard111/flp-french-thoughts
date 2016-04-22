<?php

namespace ThoughtBundle\Controller;

use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Sonata\UserBundle\Controller\ResettingFOSUser1Controller as BaseController;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Request;

/**
 * Class ResettingFOSUser1Controller.
 *
 *
 * @author Hugo Briand <briand@ekino.com>
 */
class ResettingFOSUser1Controller extends BaseController
{
    /**
     * @return RedirectResponse|\Symfony\Component\HttpFoundation\Response
     *
     * @Route("/resetting/check-email", name="user_resetting_send_email")
     */
    public function checkEmailAction()
    {
        var_dump($_REQUEST);

        $session = $this->container->get('session');
        $email = $session->get(static::SESSION_EMAIL);
        $session->remove(static::SESSION_EMAIL);

        if (empty($email)) {
            // the user does not come from the sendEmail action
            return new RedirectResponse($this->container->get('router')->generate('fos_user_resetting_request'));
        }

        return $this->container->get('templating')->renderResponse('FOSUserBundle:Resetting:checkEmail.html.'.$this->getEngine(), array(
            'email' => @$_POST['username'],
        ));
    }
}
