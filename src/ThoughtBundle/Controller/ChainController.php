<?php

namespace ThoughtBundle\Controller;

use Symfony\Bundle\FrameworkBundle\Controller\Controller;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Annotation\Route;
use ThoughtBundle\Entity\Chain;
use ThoughtBundle\Entity\ChainComment;
use ThoughtBundle\Entity\ThoughtChain;
use ThoughtBundle\Form\ChainCommentType;
use ThoughtBundle\Service\Mail;

/**
 * Class ChainController
 * @package ThoughtBundle\Controller
 *
 * @Route(path="/chain")
 */
class ChainController extends Controller
{
    /**
     * @Route("/{chainId}", name="chain_page", requirements={"chainId"="\d+"})
     *
     * @param Request $request
     * @param int $chainId
     * @throws \Exception
     * @return \Symfony\Component\HttpFoundation\RedirectResponse|\Symfony\Component\HttpFoundation\Response
     */
    public function chainListAction(Request $request, $chainId)
    {

        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $this->get('translator')->trans('thought.chain.not_exist');
            return $this->redirect($this->generateUrl('thought_homepage_index'));
        }
        if (!$this->getUser()) {

            return $this->redirect($this->generateUrl('thought_homepage_index'));
        }
        else {

            if ($chain->getIsPrivate() && $this->getUser()->getId() != $chain->getUser()->getId()) {
                $this->addFlash('success', $this->get('translator')->trans('thought.chain.access_denied'));
                return $this->redirect($this->generateUrl('thought_homepage_index'));
            }
        }

        $chainComment = new ChainComment();
        $chainComment->setChain($chain);
        $chainComment->setUser($this->getUser());

        $form = $this->createForm(new ChainCommentType(), $chainComment);

        if ($request->getMethod() == 'POST') {
            $form->handleRequest($request);

            if ($form->isValid()) {
                $em->persist($chainComment);
                $em->flush();

                $this->get('thought.service.mail_service')->mailAddNewChainComment($chainComment);

                $this->addFlash('success', $this->get('translator')->trans('thought.chain.successfully-commented'));

                return $this->redirect($this->generateUrl('chain_page', array('chainId' => $chainId)));
            } else {
                $this->addFlash('success', $this->get('translator')->trans('thought.chain.comment.not_add'));
            }
        }

        $thoughtChains = $em->getRepository('ThoughtBundle:ThoughtChain')->getSortingThoughtChain($chain);

        $collectiveChains = $em->getRepository('ThoughtBundle:Chain')->findBy([
            'isCollective'  => true
        ]);
        return $this->render('@Thought/chainPage.html.twig', array(
            'chain'         => $chain,
            'form'          => $form->createView(),
            'thoughtChains' => $thoughtChains,
            'colChains'     => $collectiveChains,
            'chainId'       => $chainId
        ));
    }

    /**
     * @Route("/add-quote", name="chain_add_quote", options={"expose"=true})
     *
     * @param Request $request
     * @return JsonResponse
     * @throws \Doctrine\ORM\NonUniqueResultException
     * @throws \Twig_Error
     */
    public function addQuoteToChain(Request $request)
    {
        $success = true;
        $message = array();

        $chainId = $request->query->get('collective_chain');

        if (!$chainId) {
            $chainId = $request->query->get('chain');
        }

        $thoughtId = $request->query->get('quote');

        if (!$chainId) {
            return new JsonResponse(array(
                'success' => false,
                'message'  => array($this->get('translator')->trans('thought.chain.not_exist')),
            ));
        }

        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.chain.not_exist');
        }

        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        if (!$thought) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.not_found');
        }

        if ($success) {
            $chainThought = $em->getRepository('ThoughtBundle:ThoughtChain')->findOneBy(array(
                'chain'   => $chain,
                'thought' => $thought,
            ));

            if (!$chainThought) {
                $lastLinkChain = $em->getRepository('ThoughtBundle:ThoughtChain')->getLastLinkChain($chain);

                $sortIndex = $lastLinkChain ? $lastLinkChain->getSortIndex() + 1 : 1;

                $chainThought = new ThoughtChain();
                $chainThought->setThought($thought);
                $chainThought->setChain($chain);
                $chainThought->setSortIndex($sortIndex);


                /** @var Mail $serviceMail */

                $user = $chain->getUser();
                $curUser = $this->getUser();

                if ($chain->getisCollective() == true) {

                    $chainThought->setUser($this->getUser());

                    $serviceMail = $this->container->get('thought.service.mail_service');
                    $serviceMail->notificationMail($user, $curUser, $chain, $thought);
                }

                $em->persist($chainThought);
                $em->flush();
            }
            $message[] = $this->get('translator')->trans('thought.chain.quote_add_chain');
        }

        return new JsonResponse(array(
            'success' => $success,
            'message' => $message,
        ));
    }

    /**
     * @Route("/remove-quote", name="chain_remove_quote", options={"expose"=true})
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function removeQuoteToChain(Request $request)
    {
        $success = true;
        $message = array();

        $chainId = $request->query->get('chain');
        $thoughtId = $request->query->get('quote');

        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.chain.not_exist');
        }

        if ($chain->getUser()->getId() != $this->getUser()->getId()) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.chain.access_denied');
        }

        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        if (!$thought) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.not_found');
        }

        if ($success) {
            $chainThought = $em->getRepository('ThoughtBundle:ThoughtChain')->findOneBy(array(
                'chain'   => $chain,
                'thought' => $thought,
            ));

            if ($chainThought) {
                $em->remove($chainThought);
                $em->flush();

                $this->get('thought.model.thoughtChain_model')->thoughtChainSort($chain);

                $message[] = $this->get('translator')->trans('thought.chain.successfully-removed');
            } else {
                $success = false;
                $message[] = $this->get('translator')->trans('thought.chain.chain-thought-not-exist');
            }
        }

        return new JsonResponse(array(
            'success' => $success,
            'message' => $message,
        ));
    }

    /**
     * @Route("/upper-quote", name="chain_upper_quote", options={"expose"=true})
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function upperQuoteToChain(Request $request)
    {
        $success = true;
        $message = array();

        $chainId = $request->query->get('chain');
        $thoughtId = $request->query->get('quote');

        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.chain.not_exist');
        }

        if ($chain->getUser()->getId() != $this->getUser()->getId()) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.chain.access_denied');
        }

        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        if (!$thought) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.not_found');
        }

        if ($success) {
            $chainThought = $em->getRepository('ThoughtBundle:ThoughtChain')->findOneBy(array(
                'chain'   => $chain,
                'thought' => $thought,
            ));

            if ($chainThought) {
                if ($chainThought->getSortIndex() > 1) {
                    $chainThought->setSortIndex(0);

                    $em->persist($chainThought);
                    $em->flush();

                    $message[] = $this->get('translator')->trans('thought.chain.successfully-upper');

                    $this->get('thought.model.thoughtChain_model')->thoughtChainSort($chain);
                } else {
                    $message[] = $this->get('translator')->trans('thought.chain.successfully-upper');
                }
            } else {
                $success = false;
                $message[] = $this->get('translator')->trans('thought.chain.chain-thought-not-exist');
            }
        }

        return new JsonResponse(array(
            'success' => $success,
            'message' => $message,
        ));
    }

    /**
     * @Route("/lower-quote", name="chain_lower_quote", options={"expose"=true})
     * @param Request $request
     * @return JsonResponse
     * @throws \Doctrine\ORM\NonUniqueResultException
     */
    public function lowerQuoteToChain(Request $request)
    {
        $success = true;
        $message = array();

        $chainId = $request->query->get('chain');
        $thoughtId = $request->query->get('quote');

        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.chain.not_exist');
        }

        if ($chain->getUser()->getId() != $this->getUser()->getId()) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.chain.access_denied');
        }

        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        if (!$thought) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.not_found');
        }

        if ($success) {
            $chainThought = $em->getRepository('ThoughtBundle:ThoughtChain')->findOneBy(array(
                'chain' => $chain,
                'thought' => $thought,
            ));

            if ($chainThought) {
                $lastThought = $em->getRepository('ThoughtBundle:ThoughtChain')
                    ->getLastLinkChain($chain);

                if ($lastThought && $lastThought->getId() != $chainThought->getId()) {
                    $chainThought->setSortIndex($lastThought->getSortIndex() + 1);

                    $em->persist($chainThought);
                    $em->flush();

                    $message[] = $this->get('translator')->trans('thought.chain.successfully-lower');

                    $this->get('thought.model.thoughtChain_model')->thoughtChainSort($chain);
                } else {
                    $message[] = $this->get('translator')->trans('thought.chain.error-move');
                }
            } else {
                $success = false;
                $message[] = $this->get('translator')->trans('thought.chain.chain-thought-not-exist');
            }
        }

        return new JsonResponse(array(
            'success' => $success,
            'message' => $message,
        ));
    }

    /**
     * @Route("/up-quote", name="chain_up_quote", options={"expose"=true})
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function upQuoteToChain(Request $request)
    {
        $success = true;
        $message = array();

        $chainId = $request->query->get('chain');
        $thoughtId = $request->query->get('quote');

        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.chain.not_exist');
        }

        if ($chain->getUser()->getId() != $this->getUser()->getId()) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.chain.access_denied');
        }

        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        if (!$thought) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.not_found');
        }

        if ($success) {
            $chainThought = $em->getRepository('ThoughtBundle:ThoughtChain')->findOneBy(array(
                'chain' => $chain,
                'thought' => $thought,
            ));

            if ($chainThought) {
                if ($chainThought->getSortIndex() > 1) {
                    $siblingChainThought = $em->getRepository('ThoughtBundle:ThoughtChain')->findOneBy(array(
                        'chain'     => $chain,
                        'sortIndex' => $chainThought->getSortIndex() - 1,
                    ));

                    if ($siblingChainThought) {
                        $chainThought->setSortIndex($chainThought->getSortIndex() - 1);
                        $em->persist($chainThought);

                        $siblingChainThought->setSortIndex($siblingChainThought->getSortIndex() + 1);
                        $em->persist($siblingChainThought);

                        $em->flush();

                        $message[] = $this->get('translator')->trans('thought.chain.successfully-up');
                    } else {
                        $message[] = $this->get('translator')->trans('thought.chain.error-move');
                    }
                } else {
                    $success = false;
                    $message[] = $this->get('translator')->trans('thought.chain.error-up-first-elem');
                }
            } else {
                $success = false;
                $message[] = $this->get('translator')->trans('thought.chain.chain-thought-not-exist');
            }
        }

        return new JsonResponse(array(
            'success' => $success,
            'message' => $message,
        ));
    }

    /**
     * @Route("/down-quote", name="chain_down_quote", options={"expose"=true})
     *
     * @param Request $request
     * @return JsonResponse
     */
    public function downQuoteToChain(Request $request)
    {
        $success = true;
        $message = array();

        $chainId = $request->query->get('chain');
        $thoughtId = $request->query->get('quote');

        $em = $this->getDoctrine()->getManager();

        $chain = $em->getRepository('ThoughtBundle:Chain')->find($chainId);

        if (!$chain) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.chain.not_exist');
        }

        if ($chain->getUser()->getId() != $this->getUser()->getId()) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.chain.access_denied');
        }

        $thought = $em->getRepository('ThoughtBundle:Thought')->find($thoughtId);

        if (!$thought) {
            $success = false;
            $message[] = $this->get('translator')->trans('thought.not_found');
        }

        if ($success) {
            $chainThought = $em->getRepository('ThoughtBundle:ThoughtChain')->findOneBy(array(
                'chain' => $chain,
                'thought' => $thought,
            ));

            if ($chainThought) {
                $sibling = $em->getRepository('ThoughtBundle:ThoughtChain')->findOneBy(array(
                    'chain' => $chain,
                    'sortIndex' => $chainThought->getSortIndex() + 1,
                ));

                if ($sibling) {
                    $chainThought->setSortIndex($chainThought->getSortIndex() + 1);
                    $em->persist($chainThought);

                    $sibling->setSortIndex($sibling->getSortIndex() - 1);
                    $em->persist($chainThought);

                    $em->flush();

                    $message[] = $this->get('translator')->trans('thought.chain.successfully-down');
                } else {
                    $success = false;
                    $message[] = $this->get('translator')->trans('thought.chain.error-down-last-elem');
                }
            } else {
                $success = false;
                $message[] = $this->get('translator')->trans('thought.chain.chain-thought-not-exist');
            }
        }

        return new JsonResponse(array(
            'success' => $success,
            'message' => $message,
        ));
    }

    /**
     * @Route("/comment/{commentId}/remove", name="chain_comment_remove", requirements={"commentId"="\d+"})
     *
     * @param int $commentId
     * @return \Symfony\Component\HttpFoundation\RedirectResponse
     */
    public function removeCommentAction($commentId)
    {
        $em = $this->getDoctrine()->getManager();

        $comment = $em->getRepository('ThoughtBundle:ChainComment')->find($commentId);

        if (!$comment) {
            $this->addFlash('success', $this->get('translator')->trans('thought.chain.comment.not_found'));

            return $this->redirect($this->generateUrl('thought_homepage_index'));
        }

        try {
            $em->remove($comment);
            $em->flush();

            $this->addFlash('success', $this->get('translator')->trans('thought.comment.deleted'));
        } catch (\Exception $e) {
            $this->addFlash('success', $e->getMessage());
        }

        return $this->redirect($this->generateUrl('chain_page', array('chainId' => $comment->getChain()->getId())));
    }
}
