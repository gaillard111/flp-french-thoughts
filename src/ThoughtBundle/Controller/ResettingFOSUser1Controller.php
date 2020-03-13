<?php

namespace ThoughtBundle\Controller;

use Application\Sonata\UserBundle\Entity\User;
use FOS\UserBundle\Util\TokenGeneratorInterface;
use Sensio\Bundle\FrameworkExtraBundle\Configuration\Route;
use Sonata\UserBundle\Controller\ResettingFOSUser1Controller as BaseController;
use Symfony\Component\HttpFoundation\RedirectResponse;
use Symfony\Component\HttpFoundation\Response;
use Twig_Error;

/**
 * Class ResettingFOSUser1Controller.
 */
class ResettingFOSUser1Controller extends BaseController
{
    /**
     * Request reset user password: submit form and send email
     *
     * @return RedirectResponse|Response
     *
     * @throws Twig_Error
     * @Route("/resetting/send-email", name="user_resetting_send_email")
     */
    public function sendEmailAction()
    {
        $username = $this->container->get('request')->request->get('username');

        /** @var $user User */
        $user = $this->container->get('fos_user.user_manager')->findUserByUsernameOrEmail($username);

        if (null === $user) {
            return $this->container->get('templating')->renderResponse('FOSUserBundle:Resetting:request.html.' . $this->getEngine(), ['invalid_username' => $username]);
        }

        if ($user->isPasswordRequestNonExpired($this->container->getParameter('fos_user.resetting.token_ttl'))) {
            return $this->container->get('templating')->renderResponse('FOSUserBundle:Resetting:passwordAlreadyRequested.html.' . $this->getEngine());
        }

        if (null === $user->getConfirmationToken()) {
            /** @var $tokenGenerator TokenGeneratorInterface */
            $tokenGenerator = $this->container->get('fos_user.util.token_generator');
            $user->setConfirmationToken($tokenGenerator->generateToken());
        }

        $this->container->get('session')->set(static::SESSION_EMAIL, $user);
        $this->container->get('fos_user.mailer')->sendResettingEmailMessage($user);
        $user->setPasswordRequestedAt(new \DateTime());
        $this->container->get('fos_user.user_manager')->updateUser($user);

        return new RedirectResponse($this->container->get('router')->generate('fos_user_resetting_check_email'));
    }
}
