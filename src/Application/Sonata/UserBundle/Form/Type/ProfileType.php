<?php

namespace Application\Sonata\UserBundle\Form\Type;

use Symfony\Component\Form\AbstractType;
use Symfony\Component\Form\FormBuilderInterface;
use Symfony\Component\OptionsResolver\OptionsResolver;
use Symfony\Component\OptionsResolver\OptionsResolverInterface;

/**
 * Class ProfileType
 * @package Application\Sonata\UserBundle\Form\Type
 */
class ProfileType extends AbstractType
{
    /**
     * @var string
     */
    private $class;

    /**
     * @param string $class The User class name
     */
    public function __construct($class)
    {
        $this->class = $class;
    }

    /**
     * @param FormBuilderInterface $builder
     * @param array                $options
     */
    public function buildForm(FormBuilderInterface $builder, array $options)
    {
        $builder
            ->add('firstname', null, array(
                'label'    => 'user.form.profile.firstname.label',
                'label_attr' => array(
                    'class' => 'control-label col-sm-2',
                ),
                'attr' => array(
                    'class' => 'form-control',
                ),
                'required' => false,
                'translation_domain' => 'messages',
            ))
            ->add('lastname', null, array(
                'label'    => 'user.form.profile.lastname.label',
                'label_attr' => array(
                    'class' => 'control-label col-sm-2',
                ),
                'attr' => array(
                    'class' => 'form-control',
                ),
                'required' => false,
                'translation_domain' => 'messages',
            ))
            ->add('email', null, array(
                'label' => 'user.form.profile.email.label',
                'label_attr' => array(
                    'class' => 'control-label col-sm-2',
                ),
                'attr' => array(
                    'class' => 'form-control',
                ),
                'translation_domain' => 'messages',
            ))
        ;
    }

    /**
     * {@inheritdoc}
     */
    public function configureOptions(OptionsResolver $resolver)
    {
        $resolver->setDefaults(array(
            'data_class' => $this->class,
        ));
    }

    /**
     * {@inheritdoc}
     */
    public function getBlockPrefix()
    {
        return 'application_sonata_user_profile';
    }

    /**
     * {@inheritdoc}
     */
    public function getName()
    {
        return $this->getBlockPrefix();
    }
}
